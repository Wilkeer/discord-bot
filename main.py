import discord
from discord.ext import commands
import re
import os

TOKEN = os.getenv("DISCORD_TOKEN")

# IDs fixos
GUILD_ID = 1324960249697796106
CANAL_SETAR_ID = 1324960250033606716
CANAL_LOGS_ID = 1388228086096724098
CARGO_MEMBRO_ID = 1324960249697796112

# Farm
CARGO_GERENTE_FARM_ID = 1324960249706315826
CARGO_FARM_OK_ID = 1388321642110914600
CATEGORIA_FARM_ID = 1388331020968788030  # Categoria existente "Meu Farm"
CANAL_FARM_ORIGINAL_ID = 1388315517969760417

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# --------------------- SETAR (REGISTRO) ---------------------

class RegistroModal(discord.ui.Modal, title="Formulário de Registro"):
    nome = discord.ui.TextInput(label="Nome", placeholder="Digite seu nome In-Game", max_length=50)
    id_moto = discord.ui.TextInput(label="ID", placeholder="Digite seu ID In-Game", max_length=20)
    telefone = discord.ui.TextInput(label="Telefone", placeholder="Digite seu telefone In-Game", max_length=20, required=False)

    def __init__(self, member: discord.Member, registrado_por: discord.Member):
        super().__init__()
        self.member = member
        self.registrado_por = registrado_por

    async def on_submit(self, interaction: discord.Interaction):
        novo_apelido = f"{self.nome.value} | {self.id_moto.value}"
        try:
            await self.member.edit(nick=novo_apelido)
            print(f"[SETAR] ✅ Apelido definido: {novo_apelido}")
        except Exception as e:
            print(f"[SETAR] ❌ Erro ao definir apelido: {e}")

        cargo = interaction.guild.get_role(CARGO_MEMBRO_ID)
        if cargo:
            try:
                await self.member.add_roles(cargo)
                print(f"[SETAR] ✅ Cargo 'Membro' adicionado a {self.member}")
            except Exception as e:
                print(f"[SETAR] ❌ Erro ao adicionar cargo: {e}")

        canal_logs = interaction.guild.get_channel(CANAL_LOGS_ID)
        if canal_logs:
            try:
                embed = discord.Embed(
                    title="🛠️ Registro Realizado",
                    description="Um novo membro foi registrado no Moto Clube!",
                    color=discord.Color.dark_green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_author(name=self.member.display_name, icon_url=self.member.display_avatar.url)
                embed.add_field(name="🧾 Nome", value=f"```{self.nome.value}```", inline=False)
                embed.add_field(name="🆔 ID", value=f"```{self.id_moto.value}```", inline=False)
                embed.add_field(name="📞 Telefone", value=f"```{self.telefone.value or 'Não informado'}```", inline=False)
                embed.set_footer(text=f"Registrado por: {self.registrado_por.display_name}", icon_url=self.registrado_por.display_avatar.url)
                await canal_logs.send(embed=embed)
                print(f"[SETAR] ✅ Log enviado no canal {canal_logs.name}")
            except Exception as e:
                print(f"[SETAR] ❌ Erro ao enviar log: {e}")
        else:
            print("[SETAR] ⚠️ Canal de logs não encontrado.")

        await interaction.response.send_message("✅ Registro concluído com sucesso!", ephemeral=True)



class RegistroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Registrar", style=discord.ButtonStyle.primary, emoji="📝", custom_id="botao_registrar")
    async def registrar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RegistroModal(interaction.user, registrado_por=interaction.user)
        await interaction.response.send_modal(modal)


# --------------------- FARM ---------------------

class FarmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Criar Pasta Farm", style=discord.ButtonStyle.success, emoji="🌾", custom_id="botao_criar_farm")
    async def criar_farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        print(f"[FARM] Usuário {member} iniciou criação da pasta.")

        if guild.get_role(CARGO_FARM_OK_ID) in member.roles:
            print(f"[FARM] 🚫 {member} já possui a role FARM OK.")
            await interaction.response.send_message("🚫 Você já possui uma pasta farm criada.", ephemeral=True)
            return

        apelido = member.nick or member.name
        apelido_formatado = re.sub(r'[^a-zA-Z0-9\-]', '-', apelido)
        apelido_formatado = re.sub(r'-+', '-', apelido_formatado).strip('-')
        nome_canal = f"📁・farm-{apelido_formatado}".lower()

        categoria = guild.get_channel(CATEGORIA_FARM_ID)
        if not isinstance(categoria, discord.CategoryChannel):
            print("[FARM] ❌ Categoria inválida.")
            await interaction.response.send_message("❌ Categoria de farm não encontrada ou inválida.", ephemeral=True)
            return

        try:
            bot_role = guild.me.top_role
            canal = await guild.create_text_channel(
                name=nome_canal,
                category=categoria,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                    guild.get_role(CARGO_GERENTE_FARM_ID): discord.PermissionOverwrite(view_channel=True),
                    bot_role: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_messages=True,
                    read_message_history=True,
                    manage_roles=True
        )
    }
)
            print(f"[FARM] ✅ Canal criado: {canal.name}")

            embed = discord.Embed(
                title="📋 Meta da Farm",
                description="""Esta são suas metas de farm diário!\n\n✍️ Edite aqui suas metas diárias.""",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Pasta criada para: {apelido}")
            msg = await canal.send(embed=embed)
            await msg.pin()
            print("[FARM] ✅ Embed enviada e fixada.")

            await member.add_roles(guild.get_role(CARGO_FARM_OK_ID))
            print(f"[FARM] ✅ Cargo FARM OK adicionado para {member}.")

            canal_farm = guild.get_channel(CANAL_FARM_ORIGINAL_ID)
            if canal_farm:
                await canal_farm.set_permissions(member, view_channel=False)
                print("[FARM] ✅ Canal original ocultado.")

            canal_logs = guild.get_channel(CANAL_LOGS_ID)
            if canal_logs:
                try:
                    log_embed = discord.Embed(
                        title="📁 Pasta Farm Criada",
                        description="Uma nova pasta de farm foi criada!",
                        color=discord.Color.orange(),
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
                    log_embed.add_field(name="👤 Membro", value=f"```{member.display_name}```", inline=False)
                    log_embed.add_field(name="📂 Canal", value=f"{canal.mention}", inline=False)
                    log_embed.set_footer(text=f"Criado por: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
                    await canal_logs.send(embed=log_embed)
                    print("[FARM] ✅ Log enviado com sucesso.")
                except Exception as e:
                    print(f"[FARM] ❌ Erro ao enviar log: {e}")
            else:
                print("[FARM] ⚠️ Canal de log não encontrado.")

            await interaction.response.send_message("✅ Sua pasta foi criada com sucesso!", ephemeral=True)

        except discord.Forbidden:
            print("[FARM] ❌ Permissão insuficiente para criar canal.")
            await interaction.response.send_message("❌ Não tenho permissão para criar canal na categoria.", ephemeral=True)
        except Exception as e:
            print(f"[FARM] ❌ Erro inesperado: {e}")
            await interaction.response.send_message("❌ Ocorreu um erro ao criar sua pasta farm.", ephemeral=True)

@bot.tree.command(name="verificar_permissoes", description="Verifica as permissões do bot no canal atual", guild=discord.Object(id=GUILD_ID))
async def verificar_permissoes(interaction: discord.Interaction):
    perms = interaction.channel.permissions_for(interaction.guild.me)

    permissoes_importantes = {
        "gerenciar_canais": perms.manage_channels,
        "gerenciar_permissoes": perms.manage_roles,
        "criar_conversas": perms.create_private_threads or perms.create_public_threads,  # redundância para threads
        "ver_canal": perms.view_channel,
        "enviar_mensagens": perms.send_messages,
        "fixar_mensagens": perms.manage_messages,
        "atribuir_cargos": perms.manage_roles,
    }

    embed = discord.Embed(
        title="🔍 Permissões do Bot no Canal Atual",
        color=discord.Color.blurple()
    )

    for nome, valor in permissoes_importantes.items():
        status = "✅" if valor else "❌"
        embed.add_field(name=nome.replace("_", " ").title(), value=status, inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# --------------------- EVENTOS E COMANDOS ---------------------

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")
    bot.add_view(RegistroView())
    bot.add_view(FarmView())
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("📌 Comandos sincronizados com sucesso.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


@bot.tree.command(name="setar", description="Reenvia o formulário de registro", guild=discord.Object(id=GUILD_ID))
async def setar(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("🚫 Você não tem permissão para usar este comando.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Registro Moto Clube",
        description="📝 Clique no botão abaixo para se registrar no Moto Clube.",
        color=discord.Color.red()
    )
    embed.set_image(url="https://i.imgur.com/RcUNBIf.jpeg")
    await interaction.response.send_message(embed=embed, view=RegistroView())


@bot.tree.command(name="farm", description="Inicia o sistema de farm", guild=discord.Object(id=GUILD_ID))
async def farm(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌾 Sistema de Farm",
        description="Clique no botão abaixo para criar sua pasta de farm.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, view=FarmView())

bot.run(TOKEN)
