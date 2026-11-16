"""Emparejamiento, límite de intentos, ajustes por celular, copiar y olvidar."""

import json

import celulares
from celulares import Registro, id_corto


class Reloj:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t


def nuevo(tmp_path, reloj=None):
    return Registro(tmp_path, reloj=reloj or Reloj())


def test_emparejar_con_el_codigo_y_volver_con_el_token(tmp_path):
    r = nuevo(tmp_path)
    resultado, token = r.emparejar(r.codigo, "1.1.1.1")
    assert resultado == "ok" and token in r.celulares
    assert r.emparejar(token, "1.1.1.1") == ("ok", token)
    # Se guardó en el archivo: otro Registro sobre la misma carpeta lo reconoce
    assert token in nuevo(tmp_path).celulares


def test_codigo_equivocado_y_bloqueo_que_se_duplica(tmp_path):
    reloj = Reloj()
    r = nuevo(tmp_path, reloj)
    malo = "0000" if r.codigo != "0000" else "1111"
    for _ in range(celulares.INTENTOS):
        assert r.emparejar(malo, "9.9.9.9") == ("no", None)
    resultado, espera = r.emparejar(r.codigo, "9.9.9.9")  # bloqueado aunque ahora use el bueno
    assert resultado == "espera" and 0 < espera <= celulares.BLOQUEO_BASE + 1
    assert r.emparejar(r.codigo, "2.2.2.2")[0] == "ok"  # otro equipo no queda bloqueado
    reloj.t += celulares.BLOQUEO_BASE + 1
    for _ in range(celulares.INTENTOS):
        r.emparejar(malo, "9.9.9.9")
    assert r.emparejar(r.codigo, "9.9.9.9")[1] > celulares.BLOQUEO_BASE + 1  # la segunda vez, el doble


def test_muchos_fallos_cambian_el_codigo(tmp_path):
    r = nuevo(tmp_path)
    avisos = []
    r.al_cambiar_codigo = avisos.append
    for i in range(celulares.FALLOS_PARA_CAMBIAR - 1):
        r.anotar_fallo(f"10.0.0.{i % 200}")
    assert avisos == []
    r.anotar_fallo("10.0.0.250")
    assert len(avisos) == 1 and avisos[0] == r.codigo and len(r.codigo) == 4


def test_ajustes_separados_por_celular_y_borrado(tmp_path):
    r = nuevo(tmp_path)
    _, a = r.emparejar(r.codigo, "1.1.1.1")
    _, b = r.emparejar(r.codigo, "1.1.1.2")
    r.guardar_ajuste(a, 'control_completo {"el":[]}')
    r.guardar_ajuste(a, "sens 9")
    assert r.ajustes_de(a) == {"control_completo": '{"el":[]}', "sens": "9"}
    assert r.ajustes_de(b) == {}
    r.guardar_ajuste(a, "sens ")  # valor vacío = borrado (queda None para que otro celular no lo reviva)
    assert r.ajustes_de(a)["sens"] is None


def test_otros_y_copiar(tmp_path):
    r = nuevo(tmp_path)
    _, a = r.emparejar(r.codigo, "1.1.1.1")
    _, b = r.emparejar(r.codigo, "1.1.1.2")
    r.poner(a, "nombre", "Celu A")
    r.guardar_ajuste(a, "noche 1")
    otros = r.otros(b)
    assert [o["nombre"] for o in otros] == ["Celu A"] and r.otros(a) == []
    assert r.copiar(b, otros[0]["id"]) and r.ajustes_de(b) == {"noche": "1"}
    assert not r.copiar(b, "no-existe") and not r.copiar(a, id_corto(a))


def test_olvidar_uno_y_todos(tmp_path):
    r = nuevo(tmp_path)
    tokens = [r.emparejar(r.codigo, f"1.1.1.{i}")[1] for i in range(3)]
    r.guardar_ajuste(tokens[0], "sens 3")
    assert r.olvidar({id_corto(tokens[0])}) == [tokens[0]]
    assert tokens[0] not in r.celulares and tokens[0] not in r.ajustes["celulares"]
    assert r.emparejar(tokens[0], "1.1.1.0")[0] == "no"  # perdió el permiso
    assert len(r.olvidar(None)) == 2 and r.celulares == {}


def test_formatos_viejos_se_convierten(tmp_path):
    (tmp_path / "tokens.json").write_text(json.dumps(["tok1", "tok2"]), "utf-8")
    (tmp_path / "ajustes.json").write_text(json.dumps({"modelo": "alargado"}), "utf-8")
    r = nuevo(tmp_path)
    assert set(r.celulares) == {"tok1", "tok2"} and r.celulares["tok1"]["nombre"] == "Celular 1"
    assert r.ajustes == {"celulares": {}}  # los ajustes viejos no se le dan a nadie...
    viejo = json.loads((tmp_path / "ajustes-formato-viejo.json").read_text("utf-8"))
    assert viejo == {"modelo": "alargado"}  # ...quedan de respaldo


def test_lista_para_el_icono(tmp_path):
    r = nuevo(tmp_path)
    _, a = r.emparejar(r.codigo, "1.1.1.1")
    r.poner(a, "nombre", "SM-A065M")
    lista = r.lista({a})
    assert lista == [{"id": id_corto(a), "nombre": "SM-A065M", "visto": lista[0]["visto"], "conectado": True}]
