-- ------------------------------------------------------------------------------------------
-- USUÁRIOS
-- ------------------------------------------------------------------------------------------

TRUNCATE usuarios, pedidos, empresas, produtos RESTART IDENTITY CASCADE;

INSERT INTO empresas (nome, cnpj, usuario, senha)
VALUES (
    'EMPRESA TESTE',
    '12345678901234',
    'empresa_teste',
    '$argon2id$v=19$m=19456,t=2,p=1$/bai1vvFUHrEH7CV9yNAsA$CWBCbWybl6iBa6NqMmmGtODd/1pTEvJYR9Uta893KhM'
);

INSERT INTO empresas (nome, cnpj, usuario, senha)
VALUES (
    'EMPRESA TESTE 2',
    '12345678901230',
    'empresa_teste1',
    '$argon2id$v=19$m=19456,t=2,p=1$/bai1vvFUHrEH7CV9yNAsA$CWBCbWybl6iBa6NqMmmGtODd/1pTEvJYR9Uta893KhM'
);

INSERT INTO produtos (nome, valor, empresa_id)
VALUES (
    'produto teste',
    24.7,
    1
);

INSERT INTO usuarios (nome, usuario, senha_hash, empresa_id, role)
VALUES (
    'Usuario 1',
    'usuario1',
    '$argon2id$v=19$m=19456,t=2,p=1$/bai1vvFUHrEH7CV9yNAsA$CWBCbWybl6iBa6NqMmmGtODd/1pTEvJYR9Uta893KhM',
    1,
    'barman'
);
 
INSERT INTO usuarios (nome, usuario, senha_hash, empresa_id, role)
VALUES (
    'Usuario 2',
    'usuario2',
    '$argon2id$v=19$m=19456,t=2,p=1$/bai1vvFUHrEH7CV9yNAsA$CWBCbWybl6iBa6NqMmmGtODd/1pTEvJYR9Uta893KhM',
    1,
    'barman'
);

INSERT INTO usuarios (nome, usuario, senha_hash, empresa_id, role)
VALUES (
    'Usuario 3',
    'usuario3',
    '$argon2id$v=19$m=19456,t=2,p=1$/bai1vvFUHrEH7CV9yNAsA$CWBCbWybl6iBa6NqMmmGtODd/1pTEvJYR9Uta893KhM',
    1,
    'barman'
);


-- ------------------------------------------------------------------------------------------
-- PEDIDOS
-- ------------------------------------------------------------------------------------------

INSERT INTO pedidos (produto, usuario_id, empresa_id, status)
VALUES (1, 1, 1, 'ABERTO');

INSERT INTO pedidos (produto, usuario_id, empresa_id, status)
VALUES (1, 1, 1, 'ENTREGUE');

INSERT INTO pedidos (produto, usuario_id, empresa_id, status)
VALUES (1, 1, 1, 'CANCELADO');