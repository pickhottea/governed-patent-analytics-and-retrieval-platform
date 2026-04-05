{% macro canonicalize_publication_number(expr) %}
upper(
    nullif(
        replace(
            replace(
                replace(
                    replace(
                        replace(
                            replace(
                                replace(
                                    replace(
                                        replace(
                                            replace(
                                                replace(
                                                    replace(
                                                        ltrim(rtrim(cast({{ expr }} as nvarchar(255)))),
                                                        char(123), ''
                                                    ),
                                                    char(125), ''
                                                ),
                                                char(39), ''
                                            ),
                                            char(34), ''
                                        ),
                                        char(36), ''
                                    ),
                                    char(58), ''
                                ),
                                '.', ''
                            ),
                            '-', ''
                        ),
                        '/', ''
                    ),
                    ' ', ''
                ),
                char(9), ''
            ),
            char(10), ''
        ),
        char(13), ''
    ),
    ''
)
{% endmacro %}