from io import BytesIO
from os import path
from urllib.parse import unquote_plus
import zipfile
from flask.testing import FlaskClient
from unittest import mock
from datetime import datetime
from app.models import Entry, Category
from app import db
from app.helpers import (
    handle_image_upload, download_giphy_image, is_valid_giphy_url, handle_image, 
    parse_date, allowed_file, get_data, create_zip
)

def test_handle_image_upload_file(mock_file: mock.Mock, test_client: FlaskClient):
    # Given: A mocked file and handle_image function
    # When: handle_image_upload is called with a file
    # Then: It should return the filename processed by handle_image
    with mock.patch('app.helpers.handle_image') as mock_handle_image:
        mock_handle_image.return_value = 'test.jpg'
        result = handle_image_upload(1, mock_file, None, 'uploads', {'jpg', 'png'})
        assert result == 'test.jpg'

def test_handle_image_upload_giphy(test_client: FlaskClient):
    # Given: A mocked download_giphy_image function
    # When: handle_image_upload is called with a GIPHY URL
    # Then: It should return the GIF filename processed by download_giphy_image
    with mock.patch('app.helpers.download_giphy_image') as mock_download_giphy_image:
        mock_download_giphy_image.return_value = '1.gif'
        result = handle_image_upload(1, None, 'https://media.giphy.com/media/test.gif', 'uploads', {'gif'})
        assert result == '1.gif'

def test_download_giphy_image_valid(test_client: FlaskClient):
    # Given: A mocked successful HTTP response for a valid GIPHY URL
    # When: download_giphy_image is called with a valid URL
    # Then: It should return the expected filename
    with mock.patch('requests.get') as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.content = b'test content'
        mock_get.return_value = mock_response

        with mock.patch('builtins.open', mock.mock_open()) as mock_file:
            with mock.patch('app.helpers.create_upload_folder'):
                result = download_giphy_image('https://media.giphy.com/media/test.gif', 1, 'uploads')
                assert result == '1.gif'

def test_download_giphy_image_invalid_url(test_client: FlaskClient):
    # Given: An invalid URL
    # When: download_giphy_image is called with this URL
    # Then: It should return None indicating failure
    result = download_giphy_image('https://invalid-url.com/media/test.gif', 1, 'uploads')
    assert result is None

def test_is_valid_giphy_url():
    # Given: Different URLs to test
    # When: Checking if URLs are valid Giphy links
    # Then: It should correctly validate the URLs
    assert is_valid_giphy_url('https://media.giphy.com/media/test.gif')
    assert not is_valid_giphy_url('https://invalid-url.com/media/test.gif')

def test_handle_image_valid(mock_file: mock.Mock, test_client: FlaskClient):
    # Given: A file with a valid extension and mocked necessary functions
    # When: handle_image is called with a valid file
    # Then: It should return the expected filename and save the file once
    with mock.patch('app.helpers.allowed_file', return_value=True):
        with mock.patch('builtins.open', mock.mock_open()):
            with mock.patch('app.helpers.create_upload_folder'):
                mock_file.save = mock.Mock()
                result = handle_image(mock_file, 1, 'uploads', {'jpg', 'png'})
                assert result == '1.jpg'
                mock_file.save.assert_called_once()

def test_handle_image_invalid_extension(mock_file: mock.Mock, test_client: FlaskClient):
    # Given: A file with an invalid extension
    # When: handle_image is called
    # Then: It should return None indicating failure
    with mock.patch('app.helpers.allowed_file', return_value=False):
        result = handle_image(mock_file, 1, 'uploads', {'jpg', 'png'})
        assert result is None

def test_parse_date():
    # Given: Various date strings to parse
    # When: parse_date is called
    # Then: It should return the correct date or None for invalid input
    assert parse_date('2021-05-20') == datetime(2021, 5, 20).date()
    assert parse_date('invalid-date') is None

def test_allowed_file():
    # Given: Filename and allowed extensions
    # When: Checking if a file is allowed
    # Then: It should correctly determine if the file extension is allowed
    assert allowed_file('test.jpg', {'jpg', 'png'})
    assert not allowed_file('test.txt', {'jpg', 'png'})

def test_get_data(test_client: FlaskClient, init_database: None):
    # Given: An initialized database and test_client context
    # When: get_data is called
    # Then: It should return correctly formatted entries
    with test_client.application.app_context():
        formatted_entries = get_data(db)
        assert len(formatted_entries) == 2
        entry = formatted_entries['entries'][0]
        assert entry['title'] == "John's Birthday"
        assert entry['category']['name'] == "Birthday"

def test_create_zip(test_client, init_database):
    data = {
        'categories': [{'color_hex': '#FF8A65', 'name': 'Cake', 'symbol': '🍰'}],
        'entries': [{
            'category': {'color_hex': '#FF8A65', 'name': 'Cake', 'symbol': '🍰'},
            'date': '2024-06-01',
            'image_url': '/uploads/test.jpg',
            'title': 'Old',
        }]
    }

    # Assuming the path '/uploads/test.jpg' needs to be converted to an absolute path
    # This would typically depend on how your application resolves paths
    upload_folder = '/full/path/to/uploads'
    expected_image_path = path.join(upload_folder, 'test.jpg')
    db_uri = 'sqlite:////app/data/data.db'
    expected_db_path = unquote_plus(db_uri[10:])

    # Mock the os.path.exists to always return True
    with mock.patch('os.path.exists', return_value=True):
        with mock.patch('builtins.open', mock.mock_open(read_data='test content'), create=True):
            with mock.patch('zipfile.ZipFile') as mock_zip:
                zip_file_instance = mock_zip.return_value.__enter__.return_value
                zip_file_instance.write = mock.Mock()

                # Call function
                create_zip(data, upload_folder, db_uri)

                # Check if the image and database file were correctly written to the zip
                zip_file_instance.write.assert_any_call(expected_image_path, arcname='test.jpg')
                zip_file_instance.write.assert_any_call(expected_db_path, arcname='data.db')

