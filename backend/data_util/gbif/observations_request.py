from backend.config import get_settings
from backend.config.base import BaseAppSettings
from backend.models.gbif import GBIFFormat
from datetime import datetime
from typing import Literal


def build_observations_request(
        min_date_type: Literal['modified', 'last_interpreted'],
        min_date: datetime = datetime(1800, 1, 1),
        test: bool = False) -> dict:
    """
    Creates a preformatted download request body for GBIF's 
    download request API. This request will retrieve records with values in the
    'modified' or 'last_interpreted' column which are more recent than the provided
    min_date, as well as records with no value at all.

    Args:
        min_date_type ('modified', 'last_interpreted'): Which GBIF column
            compare to database dates
        min_date (str): Datetime in ISO 8601 format used to determine the
            earliest date value for records
        test (bool): Determines use of all datasets or single dataset for testing

    Returns:
        GBIF Download Request Body (dict)
    """

    format: GBIFFormat = GBIFFormat.dwca
    settings: BaseAppSettings = get_settings()

    datasets = ["ba9984d8-d982-4fe6-b81c-a7585790034a",  # UTIC
                "96193ea2-f762-11e1-a439-00145eb45e9a",  # A&M
                "50c9509d-22c7-4a22-a47d-8c48425ef4a7",  # iNat Research-Grade
                "821cc27a-e3bb-4bc5-ac34-89ada245069d",  # National Museum Extant Specimen
                "13fdfab7-e281-428d-8c1f-e72eb7398e97",  # Texas Tech
                "297ecc07-da20-4ebf-9f41-4f80330b4b33",  # UTEP Insects
                "aae308f4-9f9c-4cdd-b4ef-c026f48be551"]  # U of Kansas Entomological Museum

    # Allowed Chordates:
    #   Thaliacea 207
    #   Ascidiacea 356
    #   Leptocardii 7375758
    #   Appendicularia 211

    # Predicates to target invertebrates
    inverts_predicates = [
        {
            "type": "or",
            "predicates": [
                {
                    "type": "not",
                    "predicate": {
                        "type": "equals",
                        "key": "PHYLUM_KEY",
                        "value": "44"
                    }
                },
                {
                    "type": "in",
                    "key": "CLASS_KEY",
                    "values": [
                        "207",
                        "356",
                        "211",
                        "7375758"
                    ]
                }
            ]
        },
        {
            "type": "equals",
            "key": "KINGDOM_KEY",
            "value": "1"
        },
        {
            "type": "equals",
            "key": "OCCURRENCE_STATUS",
            "value": "PRESENT"
        },
    ]

    if not test:
        all_inverts_request = {
            "creator": settings.gbif.user,
            "notificationAddresses": [
                settings.gbif.email
            ],
            "format": format,
            "sendNotification": "true",
            "predicate": {
                "type": "and",
                "predicates": [
                    *inverts_predicates,
                    {
                        "type": "in",
                        "key": "DATASET_KEY",
                        "values": datasets
                    },
                    {
                        "type": "or",
                        "predicates": [
                            {
                                "type": "greaterThanOrEquals",
                                "key": min_date_type.upper(),
                                "value": min_date.isoformat()
                            },
                            {
                                "type": "isNull",
                                "parameter": min_date_type.upper()
                            }
                        ]
                    }
                ]
            }
        }
        return all_inverts_request

    else:
        # Much smaller request (22k from UTEP) for testing
        test_inverts_request = {
            "creator": settings.gbif.user,
            "notificationAddresses": [
                settings.gbif.email
            ],
            "format": format,
            "sendNotification": "true",
            "predicate": {
                "type": "and",
                "predicates": [
                    *inverts_predicates,
                    {
                        "type": "in",
                        "key": "DATASET_KEY",
                        "values": ['297ecc07-da20-4ebf-9f41-4f80330b4b33']
                    },
                    {
                        "type": "or",
                        "predicates": [
                            {
                                "type": "greaterThanOrEquals",
                                "key": min_date_type.upper(),
                                "value": min_date.date().isoformat()
                            },
                            {
                                "type": "isNull",
                                "parameter": min_date_type.upper()
                            }
                        ]
                    }
                ]
            }
        }
        return test_inverts_request
