from datetime import date

from django.core.management.base import BaseCommand

from aadhaar.models import AadhaarDatabase


SANDBOX_AADHAAR_DATA = [
    {
        "aadhaar_number": "900000000005",
        "first_name": "Aarav",
        "middle_name": "",
        "last_name": "Mehta",
        "full_name": "Aarav Mehta",
        "date_of_birth": date(1996, 4, 14),
        "address": "12 MG Road, Indiranagar, Bengaluru, Karnataka - 560038",
        "gender": "M",
        "phone_number": "9876500005",
    },
    {
        "aadhaar_number": "900000000006",
        "first_name": "Diya",
        "middle_name": "",
        "last_name": "Sharma",
        "full_name": "Diya Sharma",
        "date_of_birth": date(1998, 9, 3),
        "address": "44 Sector 15, Noida, Uttar Pradesh - 201301",
        "gender": "F",
        "phone_number": "9876500006",
    },
    {
        "aadhaar_number": "900000000007",
        "first_name": "Rohan",
        "middle_name": "",
        "last_name": "Patel",
        "full_name": "Rohan Patel",
        "date_of_birth": date(1994, 1, 27),
        "address": "18 Navrangpura, Ahmedabad, Gujarat - 380009",
        "gender": "M",
        "phone_number": "9876500007",
    },
    {
        "aadhaar_number": "900000000008",
        "first_name": "Ishita",
        "middle_name": "",
        "last_name": "Nair",
        "full_name": "Ishita Nair",
        "date_of_birth": date(1997, 6, 18),
        "address": "205 Marine Drive, Kochi, Kerala - 682031",
        "gender": "F",
        "phone_number": "9876500008",
    },
    {
        "aadhaar_number": "900000000009",
        "first_name": "Karan",
        "middle_name": "",
        "last_name": "Singh",
        "full_name": "Karan Singh",
        "date_of_birth": date(1993, 11, 9),
        "address": "90 Model Town, Ludhiana, Punjab - 141002",
        "gender": "M",
        "phone_number": "9876500009",
    },
    {
        "aadhaar_number": "900000000010",
        "first_name": "Ananya",
        "middle_name": "",
        "last_name": "Reddy",
        "full_name": "Ananya Reddy",
        "date_of_birth": date(1999, 2, 22),
        "address": "8 Banjara Hills, Hyderabad, Telangana - 500034",
        "gender": "F",
        "phone_number": "9876500010",
    },
    {
        "aadhaar_number": "900000000011",
        "first_name": "Vivaan",
        "middle_name": "",
        "last_name": "Joshi",
        "full_name": "Vivaan Joshi",
        "date_of_birth": date(1995, 7, 5),
        "address": "55 Shivaji Nagar, Pune, Maharashtra - 411005",
        "gender": "M",
        "phone_number": "9876500011",
    },
    {
        "aadhaar_number": "900000000012",
        "first_name": "Meera",
        "middle_name": "",
        "last_name": "Kapoor",
        "full_name": "Meera Kapoor",
        "date_of_birth": date(1996, 12, 16),
        "address": "71 Rajouri Garden, New Delhi, Delhi - 110027",
        "gender": "F",
        "phone_number": "9876500012",
    },
    {
        "aadhaar_number": "900000000013",
        "first_name": "Aditya",
        "middle_name": "",
        "last_name": "Verma",
        "full_name": "Aditya Verma",
        "date_of_birth": date(1992, 3, 30),
        "address": "23 Gomti Nagar, Lucknow, Uttar Pradesh - 226010",
        "gender": "M",
        "phone_number": "9876500013",
    },
    {
        "aadhaar_number": "900000000014",
        "first_name": "Kavya",
        "middle_name": "",
        "last_name": "Iyer",
        "full_name": "Kavya Iyer",
        "date_of_birth": date(1998, 10, 12),
        "address": "39 T Nagar, Chennai, Tamil Nadu - 600017",
        "gender": "F",
        "phone_number": "9876500014",
    },
]


class Command(BaseCommand):
    help = "Seed Aadhaar sandbox data (10 temporary test records)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Delete existing sandbox Aadhaar numbers before seeding.",
        )

    def handle(self, *args, **options):
        sandbox_numbers = [item["aadhaar_number"] for item in SANDBOX_AADHAAR_DATA]

        if options["purge"]:
            deleted_count, _ = AadhaarDatabase.objects.filter(
                aadhaar_number__in=sandbox_numbers
            ).delete()
            self.stdout.write(f"Deleted {deleted_count} existing sandbox records.")

        created = 0
        updated = 0
        for entry in SANDBOX_AADHAAR_DATA:
            aadhaar_number = entry["aadhaar_number"]
            defaults = {k: v for k, v in entry.items() if k != "aadhaar_number"}
            _, was_created = AadhaarDatabase.objects.update_or_create(
                aadhaar_number=aadhaar_number,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sandbox Aadhaar seeding complete. created={created}, updated={updated}, total={len(SANDBOX_AADHAAR_DATA)}"
            )
        )
