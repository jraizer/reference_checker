from reference_checker.parser import split_references
from reference_checker.validator import validate_references


def test_split_numbered_references():
    text = """
    [1] Silva, J. Um título científico relevante. Revista X, 2020. doi:10.1234/abc.def
    [2] Souza, M. Outro estudo importante. Journal Y, 2021. https://example.org/artigo
    """

    assert split_references(text) == [
        "Silva, J. Um título científico relevante. Revista X, 2020. doi:10.1234/abc.def",
        "Souza, M. Outro estudo importante. Journal Y, 2021. https://example.org/artigo",
    ]


def test_valid_reference_has_only_info_issues():
    reports = validate_references([
        "Silva, J.; Santos, M. Validação de referências bibliográficas em textos científicos. Revista Brasileira de Informação, 2022. doi:10.1234/rbi.2022.001"
    ])

    assert len(reports) == 1
    assert reports[0].doi == "10.1234/rbi.2022.001"
    assert reports[0].year == 2022
    assert reports[0].is_valid


def test_missing_year_and_locator_are_warnings():
    reports = validate_references(["Silva, J. Título incompleto para análise."])

    codes = {issue.code for issue in reports[0].issues}

    assert "missing_year" in codes
    assert "missing_locator" in codes
    assert not reports[0].is_valid


def test_duplicate_doi_is_error():
    references = [
        "Silva, J. Um título científico relevante. Revista X, 2020. doi:10.1234/abc.def",
        "Souza, M. Outro título de teste. Revista Y, 2021. https://doi.org/10.1234/abc.def",
    ]

    reports = validate_references(references)

    assert reports[1].duplicate_of == 1
    assert any(issue.code == "duplicate" for issue in reports[1].issues)
