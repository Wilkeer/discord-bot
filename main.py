import discord
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")

# IDs fixos
GUILD_ID = 1324960249697796106
CANAL_SETAR_ID = 1324960250033606716
CANAL_LOGS_ID = 1388228086096724098
CARGO_MEMBRO_ID = 1324960249697796112

# Farm
CARGO_00_ID = 1324960249706315828
CARGO_SUBLIDER_ID = 1324960249697796107
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
        except Exception as e:
            print(f"Erro ao mudar apelido: {e}")

        cargo = interaction.guild.get_role(CARGO_MEMBRO_ID)
        if cargo:
            try:
                await self.member.add_roles(cargo)
            except Exception as e:
                print(f"Erro ao adicionar cargo: {e}")

        canal_logs = interaction.guild.get_channel(CANAL_LOGS_ID)
        if canal_logs:
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

    @discord.ui.button(label="Criar Pasta Farm", style=discord.ButtonStyle.green, custom_id="botao_farm")
    async def criar_farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user

        cargo_farm_ok = discord.utils.get(guild.roles, name="Farm OK")
        if cargo_farm_ok in member.roles:
            await interaction.followup.send("❌ Você já tem uma pasta de farm ativa.", ephemeral=True)
            return

        categoria_id = 1388315560479035402
        categoria_mae = guild.get_channel(categoria_id)
        if not categoria_mae or not isinstance(categoria_mae, discord.CategoryChannel):
            await interaction.followup.send("❌ Categoria mãe inválida ou não encontrada.", ephemeral=True)
            return

        nome_categoria = f"farm -> {member.display_name.lower()}"
        nova_categoria = await guild.create_category_channel(nome_categoria, category=categoria_mae)

        cargo_ids_permitidos = [
            CARGO_00_ID,
            CARGO_SUBLIDER_ID,
            CARGO_GERENTE_FARM_ID,
        ]
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        for cargo_id in cargo_ids_permitidos:
            cargo = guild.get_role(cargo_id)
            if cargo:
                overwrites[cargo] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        canal_farm = await nova_categoria.create_text_channel("📋・meta-farm", overwrites=overwrites)

        embed = discord.Embed(
            title="📋 Meta de Farm",
            description="Sua meta de farm é:\n\n- 15 entregas por dia\n- 5 prints organizados\n\nBoa sorte! 🏍️",
            color=discord.Color.green()
        )

        try:
            mensagem = await canal_farm.send(content=member.mention, embed=embed)
            await mensagem.pin()
            await member.add_roles(cargo_farm_ok)
        except discord.Forbidden:
            await interaction.followup.send("❌ Permissão insuficiente para enviar mensagem na nova pasta.", ephemeral=True)
            return

        canal_original = guild.get_channel(interaction.channel.id)
        if canal_original:
            try:
                await canal_original.set_permissions(member, view_channel=False)
            except discord.Forbidden:
                await interaction.followup.send("⚠️ Não consegui ocultar o canal original de você.", ephemeral=True)

        await interaction.followup.send("✅ Tudo pronto! Boa sorte com a farm. 🏍️", ephemeral=True)


# Instâncias fixas das views (ANTES DO on_ready)
registro_view = RegistroView()
farm_view = FarmView()


# --------------------- EVENTOS E COMANDOS ---------------------

# Variáveis globais para as views
registro_view = None
farm_view = None

@bot.event
async def on_ready():
    global registro_view, farm_view

    registro_view = RegistroView()
    farm_view = FarmView()

    bot.add_view(registro_view)
    bot.add_view(farm_view)

    print(f"🤖 Bot conectado como {bot.user}")

    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("📌 Comandos sincronizados com sucesso.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
