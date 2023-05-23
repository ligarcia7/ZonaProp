from propfinder_enhanced import url_paginator


def test_first_results_page_does_not_add_suffix_to_url():
    url = "https://www.zonaprop.com.ar/departamentos-ph.html"
    assert url_paginator(url, 0) == url


def test_second_results_page_add_suffix_to_url():
    url = "https://www.zonaprop.com.ar/departamentos-ph.html"
    assert url_paginator(url, 1) == "https://www.zonaprop.com.ar/departamentos-ph-pagina-1.html"
