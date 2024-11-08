from cryptography.fernet import Fernet


chave = Fernet.generate_key()
with open("chave.key", "wb") as chave_file:
    chave_file.write(chave)

try:

    with open("chave.key", "rb") as chave_file:
        chave = chave_file.read()
    fernet = Fernet(chave)
except Exception as e:
    print("Erro ao carregar a chave:", e)
    exit(1)


dados = "1234567812345678"

try:

    dados_criptografados = fernet.encrypt(dados.encode())
    print("Dados Criptografados:", dados_criptografados)
except Exception as e:
    print("Erro ao criptografar os dados:", e)
    exit(1)

try:
    # Descriptografa os dados
    dados_descriptografados = fernet.decrypt(dados_criptografados).decode()
    print("Dados Descriptografados:", dados_descriptografados)
except Exception as e:
    print("Erro ao descriptografar os dados:", e)
    exit(1)
