/*
Purpose:
- one canonical normalization rule for publication_number
- use in silver / gold cleanup and future joins
*/

CREATE OR ALTER FUNCTION dbo.fn_normalize_publication_number
(
    @value NVARCHAR(4000)
)
RETURNS VARCHAR(255)
AS
BEGIN
    DECLARE @x NVARCHAR(4000);

    SET @x = @value;

    IF @x IS NULL
        RETURN NULL;

    SET @x = UPPER(LTRIM(RTRIM(@x)));
    SET @x = REPLACE(@x, CHAR(9), '');
    SET @x = REPLACE(@x, CHAR(10), '');
    SET @x = REPLACE(@x, CHAR(13), '');
    SET @x = REPLACE(@x, NCHAR(160), '');
    SET @x = REPLACE(@x, '.', '');
    SET @x = REPLACE(@x, ' ', '');

    RETURN CAST(@x AS VARCHAR(255));
END;
GO