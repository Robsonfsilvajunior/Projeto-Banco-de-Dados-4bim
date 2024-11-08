from pymongo import MongoClient
import hashlib
import tkinter as tk
import tkinter.messagebox
import random
from cryptography.fernet import Fernet
from datetime import datetime
import uuid
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Carregar chave de criptografia
try:
    with open("chave.key", "rb") as chave_file:
        chave = chave_file.read()
    fernet = Fernet(chave)
except Exception as e:
    print("Erro ao carregar a chave:", e)
    exit(1)

# Configuração do MongoDB
uri = "mongodb+srv://Robertin:Teste123456@cluster0.aktpx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['Projeto4BIM']
usuarios = db['usuarios']
cartao = db["cartaoverific"]

# Inicializar janela principal
app = tk.Tk()
app.title("Gerenciador de Cartões")
app.geometry("600x400")

# Cartao
cartao_selecionado = None
loginAtual = None

# Configurações do Gmail SMTP
EMAIL_ADDRESS = 'robsonfsilvajunior@gmail.com'
EMAIL_PASSWORD = 'gsfq yepc caym zphw'
codigo_verificacao = None
email_usuario = None

# Funções
def gerar_hash(valor):
    hash_obj = hashlib.sha256(valor.encode())
    return hash_obj.hexdigest()

def verificar_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

def armazenar_cartao(usuario, numero_cartao, cvv, vencimento, email):
    if not verificar_numero_cartao(numero_cartao):
        tk.messagebox.showerror("Erro", "Número de cartão inválido.")
        return 1000
    if not verificar_email(email):
        tk.messagebox.showerror("Erro", "E-mail inválido.")
        return 1000
    
    try:
        numero_criptografado = fernet.encrypt(numero_cartao.encode())
        cvv_criptografado = fernet.encrypt(cvv.encode())
        vencimento_criptografado = fernet.encrypt(vencimento.encode())
    except Exception as e:
        print("Erro ao criptografar os dados:", e)
        tk.messagebox.showerror("Erro", "Erro ao criptografar os dados.")
        return 1000

    try:
        cartao.insert_one({
            'usuario': usuario,
            "email": email,
            'numero': numero_criptografado,
            'CVV': cvv_criptografado,
            'vencimento': vencimento_criptografado
        })
        tk.messagebox.showinfo("Sucesso", "Cartão armazenado com sucesso!")
    except Exception as e:
        print("Erro ao inserir dados no banco de dados:", e)
        tk.messagebox.showerror("Erro", "Erro ao salvar os dados no banco de dados.")

def enviar_codigo_verificacao(email, codigo):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        mensagem = MIMEMultipart()
        mensagem['From'] = EMAIL_ADDRESS
        mensagem['To'] = email
        mensagem['Subject'] = 'Código de Verificação'
        
        corpo = f'Seu código de verificação é: {codigo}'
        mensagem.attach(MIMEText(corpo, 'plain'))
        
        server.sendmail(EMAIL_ADDRESS, email, mensagem.as_string())
        server.quit()
        print("Email enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        
def gerar_codigo_verificacao():
    return str(random.randint(100000, 999999))  # Código de 6 dígitos
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def verificar_numero_cartao(numero_cartao):
    return re.match(r"^\d{16}$", numero_cartao) is not None

def salvarCompra(produto, valor, quantidade):
    global loginAtual
    if not loginAtual:
        tk.messagebox.showinfo("Erro", "Usuário não autenticado.")
        return

    valor_total = valor * quantidade  # Calcula o valor total com base na quantidade
    token_temporario = str(uuid.uuid4())  # Token único para a transação
    transacao_str = f"{produto}{valor_total}{quantidade}{datetime.now()}"
    transacao_hash = gerar_hash(transacao_str)  # Hash da transação para verificação de integridade
    
    compra = {
        "id_transacao": token_temporario,
        "email": loginAtual,
        "produto": produto,
        "valor_unitario": valor,
        "quantidade": quantidade,
        "valor_total": valor_total,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "hash_transacao": transacao_hash,
        "token_temporario": token_temporario
    }
    
    try:
        db['compras'].insert_one(compra)
        tk.messagebox.showinfo("Sucesso", f"Compra de {produto} (x{quantidade}) salva com sucesso!")
    except Exception as e:
        print("Erro ao salvar a compra:", e)
        tk.messagebox.showerror("Erro", "Erro ao salvar a compra.")

def confirmarCompra(cartao_salvo):
    tk.messagebox.showinfo("Sucesso", "Compra realizada com sucesso!")
    telaComprar()

def cartaoDados():
    for widget in app.winfo_children():
        widget.destroy()

    tk.Label(app, text="NOME COMPLETO:", font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=5, sticky='e')
    global entry_nome
    entry_nome = tk.Entry(app, width=30, font=("Arial", 10))
    entry_nome.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(app, text="NUMERO DO CARTÃO:", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=5, sticky='e')
    global entry_cartao
    entry_cartao = tk.Entry(app, width=30, font=("Arial", 10))
    entry_cartao.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(app, text="CVV DO CARTÃO:", font=("Arial", 10)).grid(row=2, column=0, padx=10, pady=5, sticky='e')
    global cvv_var
    cvv_var = tk.StringVar()
    cvv_var.trace("w", limitar_cvv)
    global entry_cvv
    entry_cvv = tk.Entry(app, textvariable=cvv_var, show='*', width=30, font=("Arial", 10))
    entry_cvv.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(app, text="VENCIMENTO (MM/AA):", font=("Arial", 10)).grid(row=3, column=0, padx=10, pady=5, sticky='e')
    global expiry_var
    expiry_var = tk.StringVar()
    expiry_var.trace("w", formatar_vencimento) 
    global entry_expiry
    entry_expiry = tk.Entry(app, textvariable=expiry_var, width=30, font=("Arial", 10))
    entry_expiry.grid(row=3, column=1, padx=10, pady=5)

    def verificar_campos_vazios():
        if not entry_nome.get().strip() or not entry_cartao.get().strip() or not entry_cvv.get().strip() or not entry_expiry.get().strip():
            tk.messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
        else:
            cartaoSubmit()

    tk.Button(app, text="Enviar", command=verificar_campos_vazios, font=('Arial', 10), width=15, height=2, bg="#4CAF50", fg="white").grid(row=4, column=0, columnspan=2, pady=10)
    tk.Button(app, text="Voltar", command=lambda: telaComprar(), font=('Arial', 10), width=15, height=2, bg="#D32F2F", fg="white").grid(row=5, column=0, columnspan=2, pady=10)

def cartaoSubmit():
    global cartao_selecionado
    nomeCartao = entry_nome.get()
    numero_cartao = entry_cartao.get()
    cvv = entry_cvv.get()
    expiry = entry_expiry.get()

    var = armazenar_cartao(nomeCartao, numero_cartao, cvv, expiry, loginAtual)
    
    if var != 1000:
       cartao_selecionado = numero_cartao
       telaComprar() 
    
def limitar_cvv(*args):
    valor = cvv_var.get()
    if len(valor) > 3:
        cvv_var.set(valor[:3])

def formatar_vencimento(*args):
    valor = expiry_var.get().replace("/", "")
    if len(valor) > 4:
        valor = valor[:4]
    if len(valor) > 2:
        valor = valor[:2] + '/' + valor[2:]
    expiry_var.set(valor)

def voltartelaComprar():
   global cartao_selecionado
   cartao_selecionado = None
   menuInicial()

def telaComprar():
    global cartao_selecionado
    for widget in app.winfo_children():
        widget.destroy()

    produto1 = {"nome": "Playstation 5", "valor": 3500.0}
    produto2 = {"nome": "Xbox Series X", "valor": 4300.0}

    produtos = [produto1, produto2]
    quantidades = {produto['nome']: tk.IntVar(value=0) for produto in produtos}
    total = 0

    def atualizar_total():
        total = sum(produto['valor'] * quantidades[produto['nome']].get() for produto in produtos)
        total_label.config(text=f"Total: R${total:.2f}")
        
        if total > 0 and cartao_selecionado:
            btn_compra.config(state=tk.NORMAL, bg="#4CAF50")
        else:
            btn_compra.config(state=tk.DISABLED, bg="#CCCCCC")

    tk.Label(app, text="Escolha o produto para comprar", font=("Arial", 14)).pack(pady=10)

    for produto in produtos:
        frame_produto = tk.Frame(app)
        frame_produto.pack(pady=5)

        tk.Label(frame_produto, text=f"{produto['nome']} - R${produto['valor']}", font=('Arial', 12)).pack(side=tk.LEFT)

        quantidade_frame = tk.Frame(frame_produto)
        quantidade_frame.pack(side=tk.LEFT, padx=10)

        tk.Button(quantidade_frame, text="-", command=lambda p=produto: quantidades[p['nome']].set(max(0, quantidades[p['nome']].get() - 1)), font=('Arial', 10)).pack(side=tk.LEFT)
        tk.Entry(quantidade_frame, textvariable=quantidades[produto['nome']], width=3).pack(side=tk.LEFT)
        tk.Button(quantidade_frame, text="+", command=lambda p=produto: quantidades[p['nome']].set(quantidades[p['nome']].get() + 1), font=('Arial', 10)).pack(side=tk.LEFT)

        quantidades[produto['nome']].trace("w", lambda *args: atualizar_total())

    total_label = tk.Label(app, text=f"Total: R${total:.2f}", font=('Arial', 12))
    total_label.pack(pady=10)

    def confirmar_compra():
        for produto in produtos:
            qtd = quantidades[produto['nome']].get()
            if qtd > 0:
                salvarCompra(produto['nome'], produto['valor'], qtd)
               
    btn_compra = tk.Button(app, text="Comprar", command=confirmar_compra, font=('Arial', 12), width=30, height=2, state=tk.DISABLED, bg="#CCCCCC", fg="white")
    btn_compra.pack(pady=10)
    
    if cartao_selecionado:
       tk.Label(app, text=f"Cartão: **** **** **** {cartao_selecionado[-4:]}", font=("Arial", 10)).pack(pady=10)
       
    tk.Button(app, text="Escolher Cartão", command=cartoesSalvos, font=('Arial', 12), width=30, height=2, bg="#4CAF50", fg="white").pack(pady=10)
    tk.Button(app, text="Voltar", command=menuInicial, font=('Arial', 12), width=30, height=2, bg="#D32F2F", fg="white").pack(pady=10)

   
def voltarCartaoEscolhido(numero):
    global cartao_selecionado
    cartao_selecionado = numero
    telaComprar()
   
def escolherCartao():
    for widget in app.winfo_children():
        widget.destroy()

    tk.Label(app, text="Escolha o cartão para pagamento", font=("Arial", 14)).pack(pady=10)

    cartoes = list(cartao.find({"email": loginAtual}))

    for idx, cartao_salvo in enumerate(cartoes):
        numero_cartao_criptografado = cartao_salvo['numero']
        numero_cartao = fernet.decrypt(numero_cartao_criptografado).decode()

        cartao_display = f"**** **** **** {numero_cartao[-4:]}"
        
        tk.Button(app, text=cartao_display, command=lambda numero=numero_cartao: voltarCartaoEscolhido(numero), font=('Arial', 12), width=30, height=2).pack(pady=10)
        
    tk.Button(app, text="Adicionar Cartão", command=lambda: cartaoDados(), font=('Arial', 12), width=20, height=1, fg="black").pack(pady=10)
    tk.Button(app, text="Voltar", command=telaComprar, font=('Arial', 12), width=30, height=2, bg="#D32F2F", fg="white").pack(pady=10)

def cartoesSalvos():
    global loginAtual
    if not loginAtual:
        tk.messagebox.showinfo("Erro", "Usuário não autenticado.")
        return
    
    cartoes = list(cartao.find({"email": loginAtual}))

    if not cartoes:
        tk.messagebox.showinfo("Informação", "Nenhum cartão salvo.")
        cartaoDados()
        return

    if cartoes:
        escolherCartao()
        return
     
def loginDados():
    for widget in app.winfo_children():
        widget.destroy()

    tk.Label(app, text="Login com Verificação de Duas Etapas", font=("Arial", 14)).pack(pady=10)

    tk.Label(app, text="Email:", font=("Arial", 10)).pack()
    global entry_email
    entry_email = tk.Entry(app, width=30, font=("Arial", 10))
    entry_email.pack(pady=5)

    tk.Label(app, text="Senha:", font=("Arial", 10)).pack()
    global entry_senha
    entry_senha = tk.Entry(app, show="*", width=30, font=("Arial", 10))
    entry_senha.pack(pady=5)

    tk.Button(app, text="Login", command=loginSubmit, font=('Arial', 10), width=15, height=2, bg="#4CAF50", fg="white").pack(pady=10)
    tk.Button(app, text="Voltar", command=menuInicial, font=('Arial', 10), width=15, height=2, bg="#D32F2F", fg="white").pack(pady=10)

def loginSubmit():
    global codigo_verificacao, email_usuario

    email = entry_email.get()
    senha = entry_senha.get()

    if not email or not senha:
        tk.messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
        return

    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    usuario = usuarios.find_one({"email": email, "senha": senha_hash})

    if usuario:
        # Armazena o email e gera um código de verificação
        email_usuario = email
        codigo_verificacao = gerar_codigo_verificacao()
        
        # Envia o código por e-mail
        enviar_codigo_verificacao(email_usuario, codigo_verificacao)
        
        # Exibe a tela para o usuário digitar o código
        mostrar_tela_verificacao()
    else:
        tk.messagebox.showerror("Erro", "Email ou senha incorretos.")
        
def mostrar_tela_verificacao():
    for widget in app.winfo_children():
        widget.destroy()

    tk.Label(app, text="Digite o código de verificação enviado para seu e-mail:", font=("Arial", 10)).pack(pady=10)
    global entry_codigo
    entry_codigo = tk.Entry(app, width=30, font=("Arial", 10))
    entry_codigo.pack(pady=10)

    tk.Button(app, text="Verificar", command=verificar_codigo, font=('Arial', 10), width=15, height=2, bg="#4CAF50", fg="white").pack(pady=10)
    tk.Button(app, text="Cancelar", command=menuInicial, font=('Arial', 10), width=15, height=2, bg="#D32F2F", fg="white").pack(pady=10)

def verificar_codigo():
    global codigo_verificacao, email_usuario, loginAtual

    codigo_digitado = entry_codigo.get()

    if codigo_digitado == codigo_verificacao:
        loginAtual = email_usuario
        tk.messagebox.showinfo("Sucesso", "Login realizado com sucesso!")
        telaComprar()
    else:
        tk.messagebox.showerror("Erro", "Código de verificação incorreto.")

def appQuit():
   app.quit()
   app.destroy()

def menuInicial():
    for widget in app.winfo_children():
        widget.destroy()

    tk.Button(app, text="Login", command=loginDados, font=('Arial', 10), width=15, height=2, bg="#4CAF50", fg="white").pack(pady=10)
    tk.Button(app, text="Cadastro", command=cadastroDados, font=('Arial', 10), width=15, height=2).pack(pady=10)
    tk.Button(app, text="Sair", command=appQuit, font=('Arial', 10), width=15, height=2, bg="#D32F2F", fg="white").pack(pady=10)

def cadastroDados():
    for widget in app.winfo_children():
        widget.destroy()

    tk.Label(app, text="EMAIL:", font=("Arial", 10)).pack(pady=10)
    global entry_cadastro_email
    entry_cadastro_email = tk.Entry(app, width=30, font=("Arial", 10))
    entry_cadastro_email.pack(pady=10)

    tk.Label(app, text="SENHA:", font=("Arial", 10)).pack(pady=10)
    global entry_cadastro_senha
    entry_cadastro_senha = tk.Entry(app, show='*', width=30, font=("Arial", 10))
    entry_cadastro_senha.pack(pady=10)

    tk.Button(app, text="Cadastrar", command=cadastroSubmit, font=('Arial', 10), width=15, height=2, bg="#4CAF50", fg="white").pack(pady=10)
    tk.Button(app, text="Voltar", command=menuInicial, font=('Arial', 10), width=15, height=2, bg="#D32F2F", fg="white").pack(pady=10)

def cadastroSubmit():
    email = entry_cadastro_email.get()
    senha = entry_cadastro_senha.get()

    if not email or not senha:
        tk.messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
        return

    senha_hash = gerar_hash(senha)

    if usuarios.find_one({"email": email}):
        tk.messagebox.showerror("Erro", "Email já cadastrado.")
        return

    usuarios.insert_one({"email": email, "senha": senha_hash})
    tk.messagebox.showinfo("Sucesso", "Cadastro realizado com sucesso!")
    menuInicial()

# Inicialização do programa
loginAtual = None
menuInicial()
app.mainloop()
