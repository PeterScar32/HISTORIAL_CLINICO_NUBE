from sqlalchemy import text

TABLAS = [
    "declaraciones_p1", "antecedentes_p2", "habitos_p3", "ficha_oftalmologica",
    "fichas_psicologia", "ficha_espirometria", "ficha_cardiologia", "ficha_altura",
    "ficha_electroencefalograma", "ficha_aptitud", "ficha_aptitud_fisica",
    "historial_clinico", "ficha_osteomuscular",
]


def aplicar_migraciones(engine):
    with engine.begin() as con:
        for t in ("ficha_aptitud_fisica", "ficha_osteomuscular"):
            con.execute(text(f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS paciente_id INTEGER REFERENCES pacientes(id) ON DELETE CASCADE"))
            con.execute(text(f"UPDATE {t} f SET paciente_id = p.id FROM pacientes p WHERE f.paciente_id IS NULL AND upper(f.codigo_paciente) IN (upper(p.codigo_paciente), upper(p.ci))"))
        con.execute(text("ALTER TABLE evaluaciones ADD COLUMN IF NOT EXISTS fichas_requeridas VARCHAR"))
        for t in TABLAS:
            con.execute(text(f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS evaluacion_id INTEGER REFERENCES evaluaciones(id) ON DELETE CASCADE"))
            con.execute(text(f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS creado_en TIMESTAMP"))
            con.execute(text(f"ALTER TABLE {t} ALTER COLUMN creado_en SET DEFAULT now()"))
            con.execute(text(f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS registrado_por VARCHAR"))
            con.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{t}_evaluacion_id ON {t} (evaluacion_id)"))
        union = " UNION ".join(f"SELECT paciente_id FROM {t} WHERE evaluacion_id IS NULL AND paciente_id IS NOT NULL" for t in TABLAS)
        con.execute(text(f"""
            INSERT INTO evaluaciones (paciente_id, tipo)
            SELECT DISTINCT x.paciente_id, 'INICIAL' FROM ({union}) x
            WHERE NOT EXISTS (SELECT 1 FROM evaluaciones e WHERE e.paciente_id = x.paciente_id)
        """))
        for t in TABLAS:
            con.execute(text(f"""
                UPDATE {t} f SET evaluacion_id = (
                    SELECT max(e.id) FROM evaluaciones e WHERE e.paciente_id = f.paciente_id)
                WHERE f.evaluacion_id IS NULL AND f.paciente_id IS NOT NULL
            """))
