# GBIF downloads request body for all inverts from approved sources
from backend.config import get_settings
from backend.config.base import BaseAppSettings
from backend.models.gbif import GBIFFormat
from datetime import date, datetime
from typing import Literal

# Filtered from list of datasets on GBIF with over 1000 specimens in Texas,
# Subsets, projects (aside from TPWD), and citizen science (aside from iNaturalist) have been removed to help with quality of determinations,
# Focus on universities and institutions
APPROVED_DATASETS = [
    # iNaturalist Research-grade Observations
    "50c9509d-22c7-4a22-a47d-8c48425ef4a7",
    # Texas A & M University Insect Collection
    "96193ea2-f762-11e1-a439-00145eb45e9a",
    # Museum at Texas Tech University Invertebrate Zoology Collection
    "13fdfab7-e281-428d-8c1f-e72eb7398e97",
    # University of Texas, Biodiversity Center, Entomology Collection(UTIC)
    "ba9984d8-d982-4fe6-b81c-a7585790034a",
    # NMNH Extant Specimen Records(USNM, US)
    "821cc27a-e3bb-4bc5-ac34-89ada245069d",
    # Snow Entomological Museum Collection
    "aae308f4-9f9c-4cdd-b4ef-c026f48be551",
    # Triplehorn Insect Collection, The Ohio State University
    "84ab7b76-f762-11e1-a439-00145eb45e9a",
    # Museum of Southwestern Biology Division of Arthropods
    "9e02f8f5-ae2f-49b9-b896-ffb0260a284c",
    # C.P. Gillette Museum of Arthropod Diversity
    "323b0e80-5e4b-4cc4-936a-d93fc8cae9bc",
    # New Mexico State Collection of Arthropods
    "85378a64-2fbc-4a48-a6b4-9f421ad48f8a",
    # University of Michigan Museum of Zoology, Division of Insects
    "13e7869e-0c76-473a-a227-53d6e3d6fbf2",
    # Museum of Comparative Zoology, Harvard University
    "4bfac3ea-8763-4f4b-a71a-76a6f5f243d3",
    # Illinois Natural History Survey Insect Collection
    "68513375-3aa5-4f6f-9975-d97d56c21d61",
    # Mississippi Entomological Museum
    "9b12d595-11ea-4128-88ea-ed378eb9ea9a",
    # TPWD HARC Texas Coastal Fisheries Matagorda Bay Trawl
    "17411afb-5543-4d0a-8f36-47cb8322062e",
    # TPWD HARC Texas Coastal Fisheries Corpus Christi Bay Trawl
    "f42d2be3-1264-4b68-a3bd-39363bcc437f",
    # Field Museum of Natural History(Zoology) Insect, Arachnid and Myriapod Collection
    "7931dcab-94f1-46ce-8092-56e4335423de",
    # TPWD HARC Texas Coastal Fisheries Aransas Bay Trawl
    "d0e9b7eb-29a9-4695-bb13-22585df648a5",
    # TPWD HARC Texas Coastal Fisheries Matagorda Bay Bag Seine
    "ea09e0f4-36c4-4383-b04d-48da83a32c5c",
    # TPWD HARC Texas Coastal Fisheries San Antonio Bay Trawl
    "fcdd34e6-43cf-4fbb-a2a9-07163619b872",
    # TPWD HARC Texas Coastal Fisheries Aransas Bay Bag Seine
    "2473e9c3-624f-4cd6-bfc6-b476913790b5",
    # TPWD HARC Texas Coastal Fisheries San Antonio Bay Bag Seine
    "95b694cd-e9db-4831-b6a9-0a6d433d92c1",
    # Brigham Young University Arthropod Museum
    "ae24fb7b-af3c-478c-a1ed-2215a90793cc",
    # The Albert J. Cook Arthropod Research Collection
    "76525e81-9210-401d-a90d-5509f771c0e7",
    # TPWD HARC Texas Coastal Fisheries Lower Laguna Madre Bag Seine
    "836204c6-f8ca-49f3-be9a-afbae64ae72c",
    # TPWD HARC Texas Coastal Fisheries Corpus Christi Bay Bag Seine
    "94a6bf19-40a2-4689-ab0e-53edb30b9d36",
    # Academy of Natural Sciences Entomology Collection
    "20524cf7-66f8-49d2-a274-102e1090e502",
    # University of Alberta E. H. Strickland Entomological Museum(UASM)
    "8971dfba-f762-11e1-a439-00145eb45e9a",
    # Harold W. Manter Laboratory of Parasitology Collection(HWML) Parasite Collection(Arctos)
    "c43384a9-8d9d-40c0-8cda-40ad47d2d69d",
    # Biodiversity Research and Teaching Collections - TCWC Marine Invertebrates
    "16b0aa56-90aa-436c-bfe8-b5af83f84575",
    # Entomology Division, Yale Peabody Museum
    "96404cc2-f762-11e1-a439-00145eb45e9a",
    # University of North Texas Elm Fork Insect Collection
    "7ab6653a-c4f4-4611-9aff-2964d56a3a4d",
    # TPWD HARC Texas Coastal Fisheries Lower Laguna Madre Trawl
    "99cac79f-b9bf-42e5-88bd-68c30a595437",
    # Essig Museum of Entomology
    "5d283bb6-64dd-4626-8b3b-a4e8db5415c3",
    # TPWD HARC Texas Coastal Fisheries Upper Laguna Madre Trawl
    "cc7cd3f8-1ff5-4273-ad34-f89351392925",
    # UF Invertebrate Zoology
    "85b1cfb6-f762-11e1-a439-00145eb45e9a",
    # UTEP Insects(Arctos)
    "297ecc07-da20-4ebf-9f41-4f80330b4b33",
    # TPWD HARC Texas Coastal Fisheries Upper Laguna Madre Bag Seine
    "9dc24de5-be12-44f9-ab75-c4b62492e8da",
    # Arizona State University Hasbrouck Insect Collection
    "750b7bfc-3577-4b26-8aaf-3e4be9f0d639",
    # Denver Museum of Nature & Science - Arachnology
    "d762b508-7a70-441b-94ad-48fd77593275",
    # Arizona State University Charles W. O'Brien Collection
    "14aff274-bf79-4a74-86ce-fb8b115adbf3",
    # Malacology Collection at the Academy of Natural Sciences of Philadelphia
    "86b50d88-f762-11e1-a439-00145eb45e9a",
    # MSB Parasite Collection (Arctos)
    "78ff8409-15b9-456f-9793-291b030190a7",
    # TPWD HARC Texas Coastal Fisheries Sabine Lake Bay Trawl
    "b902eee0-ecf4-4269-8af0-0e67d753b89a",
    # TPWD HARC Texas Coastal Fisheries Sabine Lake Bag Seine
    "f46c93f2-123d-4dc3-a06e-b2faecfda2ce",
    # CAS Entomology (ENT)
    "14f3151a-e95d-493c-a40d-d9938ef62954",
    # University of Arizona Insect Collection
    "e36d0997-2f51-4718-b684-16ec092ecd82",
    # University of Minnesota Insect Collection
    "8e02e1dd-ec54-405e-b4d7-7abdecd29cc7",
    # Entomology Collection at the Natural History Museum of Utah
    "9be3b97c-bc8c-490c-8021-dc7c75408076",
    # UTEP Invertebrates (Arctos)
    "fc53a503-d180-4a63-b8a2-868d56da5420",
    # Cornell University Insect Collection (CUIC)
    "09435c69-7ec7-46f4-b52f-5131baa10143",
    # Invertebrate Zoology Collections at the Museum of Biological Diversity (OSUM)
    "a0551854-61b9-4c1b-ad08-7f10af835b6a",
    # TPWD HARC Texas Coastal Fisheries Matagorda Bay Gill Net
    "b84099fa-99ac-4e11-a8da-d09add544131",
    # Delaware Museum of Nature and Science & Mollusks
    "3ee66eb3-4786-4bda-b7f1-c145b1a57a6b",
    # Denver Museum of Nature & Science - Entomology
    "552f282a-92a6-4f41-95ef-c6537026fbeb",
    # UCM Entomology Collection
    "c53a27b8-d019-460e-8124-662b6fa14d85",
    # University of Central Florida Collection of Arthropods (UCFC)
    "262f8270-f9c2-4bc6-a562-8ed71c0790e6",
    # LACM Entomology Collection
    "0ec927cf-325a-4d63-9499-d721c734463a",
    # Florida State Collection of Arthropods
    "86760641-4425-4130-9d20-4dd1eaa5c4a4",
    # University of Michigan Museum of Zoology, Division of Mollusks
    "7dd6e9f8-f252-42c9-bd34-221716095973",
    # Northern Arizona University - Arthropod Collection
    "8a6232d7-f93e-45a3-8b16-556aa732cd39",
    # TPWD HARC Texas Coastal Fisheries, Corpus Christi Bay Gill Net
    "420ab020-3d83-4787-8f3d-f83ebb0e6ded",
    # Ohio State Acarology Laboratory (OSAL), Ohio State University
    "96b54e8c-f762-11e1-a439-00145eb45e9a",
    # NCSM Mollusk Collection
    "51c49096-dc31-4077-b35c-4510a8ee1ee8",
    # TPWD HARC Texas Coastal Fisheries San Antonio Bay Gill Net
    "d0351e80-ae78-46ea-8601-8c458282ae73",
    # Cleveland Museum of Natural History
    "6c032b27-e4fe-4bc9-8f11-6b5f864910ce",
    # Auburn University Museum of Natural History Entomology
    "bb71d4cb-6cc3-4730-a170-82912cc84475",
    # Frost Entomological Museum
    "44fb5823-c1f5-4ac7-8e06-795a09a138f2",
    # TPWD HARC Texas Coastal Fisheries Aransas Bay Gill Net
    "a6e35034-fca7-457f-888b-e6d97030dee5",
    # TPWD HARC Texas Coastal Fisheries Upper Laguna Madre Gill Net
    "9e82c117-54f1-4750-a029-2dacc9ef5158",
    # TPWD HARC Texas Coastal Fisheries Lower Laguna Madre Gill Net
    "ab8c6591-2993-4bc5-85a4-1d106897b036",
    # TPWD HARC Texas Coastal Fisheries Sabine Lake Gill Net
    "29b43457-5ebc-465c-b275-21a03cb9f148"
]


def build_observations_request(
        min_date_type: Literal['modified', 'last_interpreted'] = 'modified',
        min_date: datetime | date = datetime(1800, 1, 1),
        test: bool = False) -> dict:
    """
    Creates a preformatted download request body for GBIF's
    download request API. This request will retrieve records with values in the
    'modified' or 'last_interpreted' column which are more recent than the provided
    min_date, as well as records with no value at all.

    Args:
        min_date_type ('modified', 'last_interpreted'): Which GBIF column
            compare to database dates
        min_date (datetime | date): Datetime in ISO 8601 format used to determine the
            earliest date value for records
        test (bool): Determines use of all datasets or single dataset for testing

    Returns:
        GBIF Download Request Body (dict)
    """

    download_format: GBIFFormat = GBIFFormat.dwca
    settings: BaseAppSettings = get_settings()

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
                        "207",  # Thaliacea
                        "356",  # Ascidiacea
                        "211",  # Appendicularia
                        "7375758"  # Leptocardii
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
        # Texas bounding box
        {
            "type": "within",
            "geometry": "POLYGON((-93.5 36.5, -106.65 36.5, -106.65 25.8, -93.5 25.8, -93.5 36.5))"
        },
        {
            "type": "or",
            "predicates": [
                {
                    "type": "greaterThanOrEquals",
                    # GBIF uses all caps for MODIFIED and LAST_INTERPRETED
                    "key": min_date_type.upper(),
                    "value": min_date.strftime("%Y-%m-%d")
                },
                {
                    "type": "isNull",
                    "parameter": min_date_type.upper()
                }
            ]
        }
    ]

    # Use APPROVED_DATASETS list unless test (then just use UTEP, 22k-ish observations)
    datasets = APPROVED_DATASETS if not test else [
        '297ecc07-da20-4ebf-9f41-4f80330b4b33']

    # Return pieced together body
    return {
        "creator": settings.gbif.user,
        "notificationAddresses": [
            settings.gbif.email
        ],
        "format": download_format,
        "sendNotification": True,
        "predicate": {
            "type": "and",
            "predicates": [*inverts_predicates, {"type": "in", "key": "DATASET_KEY", "values": datasets}]
        }
    }
