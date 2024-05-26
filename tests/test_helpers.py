import pytest
from unittest import mock
from datetime import datetime
from io import BytesIO
from app.models import Entry
from app.helpers import (
    handle_image_upload, download_giphy_image, is_valid_giphy_url, handle_image, 
    parse_date, allowed_file, get_formatted_entries, create_zip
)

# Mocking functions
def test_handle_image_upload_file(mock_file, test_client):
    with mock.patch('app.helpers.handle_image') as mock_handle_image:
        mock_handle_image.return_value = 'test.jpg'
        result = handle_image_upload(1, mock_file, None, 'uploads', {'jpg', 'png'})
        assert result == 'test.jpg'

def test_handle_image_upload_giphy(test_client):
    with mock.patch('app.helpers.download_giphy_image') as mock_download_giphy_image:
        mock_download_giphy_image.return_value = '1.gif'
        result = handle_image_upload(1, None, 'https://media.giphy.com/media/test.gif', 'uploads', {'gif'})
        assert result == '1.gif'

def test_download_giphy_image_valid(test_client):
    with mock.patch('requests.get') as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.content = b'test content'
        mock_get.return_value = mock_response

        with mock.patch('builtins.open', mock.mock_open()) as mock_file:
            with mock.patch('app.helpers.create_upload_folder'):
                result = download_giphy_image('https://media.giphy.com/media/test.gif', 1, 'uploads')
                assert result == '1.gif'

def test_download_giphy_image_invalid_url(test_client):
    result = download_giphy_image('https://invalid-url.com/media/test.gif', 1, 'uploads')
    assert result is None

def test_is_valid_giphy_url():
    assert is_valid_giphy_url('https://media.giphy.com/media/test.gif')
    assert not is_valid_giphy_url('https://invalid-url.com/media/test.gif')

def test_handle_image_valid(mock_file, test_client):
    with mock.patch('app.helpers.allowed_file', return_value=True):
        with mock.patch('builtins.open', mock.mock_open()):
            with mock.patch('app.helpers.create_upload_folder'):
                mock_file.save = mock.Mock()
                result = handle_image(mock_file, 1, 'uploads', {'jpg', 'png'})
                assert result == '1.jpg'
                mock_file.save.assert_called_once()

def test_handle_image_invalid_extension(mock_file, test_client):
    with mock.patch('app.helpers.allowed_file', return_value=False):
        result = handle_image(mock_file, 1, 'uploads', {'jpg', 'png'})
        assert result is None

def test_parse_date():
    assert parse_date('2021-05-20') == datetime(2021, 5, 20).date()
    assert parse_date('invalid-date') is None

def test_allowed_file():
    assert allowed_file('test.jpg', {'jpg', 'png'})
    assert not allowed_file('test.txt', {'jpg', 'png'})

def test_get_formatted_entries(test_client, init_database):
    with test_client.application.app_context():
        entries = Entry.query.all()
        formatted_entries = get_formatted_entries(entries)
        assert len(formatted_entries) == 1
        entry = formatted_entries[0]
        assert entry['title'] == "John's Birthday"
        assert entry['category'] == "birthday"

def test_create_zip(test_client, init_database):
    entries = [
        {
            'date': '2021-05-20',
            'category': 'birthday',
            'title': "John's Birthday",
            'description': 'Birthday party',
            'image_url': 'uploads/test.jpg'
        }
    ]
    with mock.patch('os.path.exists', return_value=True):
        with mock.patch('builtins.open', mock.mock_open(read_data='test content')):
            with mock.patch('app.helpers.path.join', return_value='uploads/test.jpg'):
                with mock.patch('zipfile.ZipFile.write') as mock_write:
                    zip_buffer = create_zip(entries, 'uploads')
                    assert zip_buffer is not None
                    mock_write.assert_any_call('uploads/test.jpg', arcname='test.jpg')