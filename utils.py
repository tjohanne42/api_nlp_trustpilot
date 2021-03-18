import unicodedata
import unidecode


def remove_accents(input_str):
    """
        example :
            input_str = "Montréal, über, 12.89, Mère, Françoise, noël, 889"
            return      "Montreal, uber, 12.89, Mere, Francoise, noel, 889"
    """
    nkfd_form = unicodedata.normalize('NFKD', unidecode.unidecode(input_str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])
