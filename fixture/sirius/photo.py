from typing import List

from sirius import File


def file_fixture() -> List[dict]:
    return [
        {
            "user_id": 1,
            "file_name": "image1.jpg",
            "file_path": "/https://min.io/images/image1.jpg",
            "file_type": "jpg",
            "file_size": 1024,
        },
        {
            "user_id": 2,
            "file_name": "image2.jpg",
            "file_path": "https://min.io/images/image2.jpg",
            "file_type": "jpg",
            "file_size": 2048,
        }
    ]


files_data = file_fixture()
for file_data in files_data:
    file = File(**file_data)
