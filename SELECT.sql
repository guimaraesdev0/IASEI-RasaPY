SELECT
    *
FROM
    x1_80
WHERE
    EXISTS (
        SELECT
            1
        FROM
            x1_56
        WHERE
            x1_56."DSProcesso" = x1_80."DSProcesso"
            AND x1_56."DSGrupo" = :dsgrupo -- Filtro pelo input dsgrupo
    )
    AND EXISTS (
        SELECT
            1
        FROM
            x1_83
        WHERE
            x1_83."DSProcesso" = x1_80."DSProcesso"
    )
    AND EXISTS (
        SELECT
            1
        FROM
            x1_82
        WHERE
            x1_82."DSProcesso" = x1_80."DSProcesso"
    )
    AND EXISTS (
        SELECT
            1
        FROM
            x1_81
        WHERE
            x1_81."DSProcesso" = x1_80."DSProcesso"
    )
    AND EXISTS (
        SELECT
            1
        FROM
            x1_2
        WHERE
            x1_2."DSProcesso" = x1_80."DSProcesso"
            AND x1_2."QTAreaHA" <= :maxarea
            AND x1_2."QTAreaHA" >= :minarea
            AND x1_2."IDFaseProcesso" = :fase
    )
    AND EXISTS (
        SELECT
            1
        FROM
            x1_9
        WHERE
            x1_9."DSProcesso" = x1_80."DSProcesso"
            AND x1_9."SGUF" = :uf
            AND x1_9."IDMunicipio" = :municipio
    )
    AND EXISTS (
        SELECT
            1
        FROM
            x1_25
        WHERE
            x1_25."DSProcesso" = x1_80."DSProcesso"
            AND x1_25."IDSubstancia" = :substancia
    )
    AND "declaracao" = 1
    AND "status_entregue" = true
    AND "dt_inicio" <= '1'
    AND "dt_inicio" >= '1'
    AND "dt_publicacao" <= '1'
    AND "dt_publicacao" >= '1'
    AND "dt_fim" <= '1'
    AND "dt_fim" >= '1';
