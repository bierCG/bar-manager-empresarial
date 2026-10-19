from app.core.security.password import hash_senha, validar_senha


def test_hash_senha():
    senha = "123456"

    resultado = hash_senha(senha)

    assert resultado != senha
    assert resultado.startswith("$argon2")


def test_validar_senha():
    senha = "123456"
    hash = hash_senha(senha)

    assert validar_senha(senha, hash)


def test_validar_senha_incorreta():
    senha = "123456"
    hash = hash_senha(senha)

    assert not validar_senha("senha_errada", hash)