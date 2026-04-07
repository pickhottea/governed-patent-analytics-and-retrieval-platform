select top 100
    publication_number,
    ascii(left(publication_number, 1)) as first_char_ascii,
    ascii(substring(publication_number, 2, 1)) as second_char_ascii,
    upper(left(publication_number, 2)) as raw_authority_code
from dbo.mart_publication_country_expanded
where country_code is null;