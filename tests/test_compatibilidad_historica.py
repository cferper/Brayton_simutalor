"""Ejecuta los tests históricos aún aplicables sin restaurar la web antigua.

Los once archivos originales permanecen completos en ``legacy_tests`` y son
idénticos a los del repositorio congelado de gas perfecto. El inventario
explícito distingue 37 contratos Flask obsoletos de las comprobaciones
matemáticas, de presentación histórica y de seguridad que siguen siendo
útiles. No se usan ``skip`` ni ``expectedFailure``.
"""

import importlib.util
from pathlib import Path
import unittest


LEGACY_DIR = Path(__file__).resolve().parents[1] / "legacy_tests"

# Sólo contratos incompatibles identificados en el diagnóstico del milestone 30.
# Cualquier test no incluido aquí sigue ejecutándose con unittest.
CONTRATOS_FLASK_ANTIGUOS = {
    "test_diagnostico_integracion": {
        "test_historial_y_descarga_conservan_diagnostico_sin_recalcular",
        "test_mapa_real_celdas_y_cortes_con_ubicacion",
        "test_ofat_real_con_no_motor_y_agregacion",
        "test_segunda_ley_real_no_motor_y_actualizacion_T0",
    },
    "test_explicaciones": {"test_dashboard_comparte_textos_del_informe"},
    "test_integracion_rendimiento": {
        "test_flask_recalcula_cambios_reversibilidad_descarga_y_retencion",
    },
    "test_integridad_json_v5": {
        "test_T0_real_actualiza_exergia_sin_evaluar_puntos",
        "test_campos_obligatorios_y_estructuras_incompletas",
        "test_estudio_real_serializado_es_reutilizable",
        "test_incoherencia_de_estados_entropia_exergia_y_camara",
        "test_json_externo_malformado_o_con_tipos_invalidos_no_provoca_500",
        "test_json_interno_danado_recalcula_y_conserva_original",
        "test_none_nan_infinito_y_cadenas_no_numericas",
        "test_nueve_parametros_distintos_no_reutilizan",
        "test_tipos_incorrectos_incluidos_booleanos",
    },
    "test_mapa_diseno": {"test_flask_mapa_descarga_y_recuperacion"},
    "test_optimizacion": {"test_flask_recalcula_los_nueve_parametros_y_descarga"},
    "test_segunda_ley": {
        "test_flask_diagnostico_reutilizacion_y_descarga",
        "test_fuente_reutilizada_solo_si_coinciden_parametros",
    },
    "test_sensibilidad": {
        "test_errores_programacion_no_se_silencian",
        "test_flask_estudio_descarga_y_referencia_inviable_admitida",
        "test_formulario_errores_conserva_valores",
        "test_normal_no_ejecuta_ofat_ni_valida_controles",
    },
    "test_verificacion_integracion_web": {
        "test_cuatro_ejecuciones_reales_aisladas_y_retencion",
        "test_enrutamiento_mapa_y_configuracion_tipificada",
        "test_enrutamiento_segunda_ley_y_T0",
        "test_enrutamiento_sensibilidad_y_T0_no_aplicable",
        "test_enrutamiento_simulacion_y_nueve_entradas",
        "test_excepcion_interna_del_mapa_no_se_presenta_como_fisica",
        "test_rechazos_multiseccion_conservan_datos_y_no_generan_informes",
        "test_recuperacion_cuatro_informes_descarga_identica_sin_recalculo",
        "test_reutilizacion_segunda_ley_solo_si_nueve_entradas_coinciden",
        "test_rutas_malformadas_symlink_e_informe_incompleto",
        "test_secciones_educativas_conectadas_sin_duplicar_formulario",
    },
    "test_verificacion_simulacion": {
        "test_formulario_porcentaje_y_no_motor_sin_informe",
    },
    "test_viabilidad": {
        "test_flask_acepta_caso_motor_con_antiguo_barrido_inviable",
        "test_flask_muestra_limite_numerico_y_conserva_datos",
    },
}


def _casos(suite):
    """Recorre TestSuite anidadas; devuelve instancias TestCase."""
    for caso in suite:
        if isinstance(caso, unittest.TestSuite):
            yield from _casos(caso)
        else:
            yield caso


def load_tests(loader, tests, pattern):
    """Pasa sólo los contratos vigentes de archivos históricos a la suite.

    ``loader``: TestLoader de unittest; ``tests``: suite descubierta;
    ``pattern``: patrón opcional de descubrimiento. Retorna TestSuite.
    Las pruebas retiradas del perfil vigente no se ejecutan silenciosamente:
    se enumeran arriba, se cuentan y se conservan en su fuente histórica.
    """
    vigentes = unittest.TestSuite()
    excluidos = 0
    for nombre, antiguos in sorted(CONTRATOS_FLASK_ANTIGUOS.items()):
        ruta = LEGACY_DIR / f"{nombre}.py"
        especificacion = importlib.util.spec_from_file_location(
            f"brayton_legacy_{nombre}", ruta
        )
        modulo = importlib.util.module_from_spec(especificacion)
        especificacion.loader.exec_module(modulo)
        casos = list(_casos(loader.loadTestsFromModule(modulo)))
        metodos = {caso._testMethodName for caso in casos}
        if not antiguos.issubset(metodos):
            raise AssertionError(
                f"El manifiesto de {nombre} ya no coincide con los tests archivados: "
                f"{sorted(antiguos - metodos)}"
            )
        for caso in casos:
            if caso._testMethodName in antiguos:
                excluidos += 1
            else:
                vigentes.addTest(caso)
    if excluidos != 37:
        raise AssertionError(f"Esperados 37 métodos Flask históricos: {excluidos}")
    return vigentes
