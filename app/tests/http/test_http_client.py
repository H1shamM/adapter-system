from pytest_mock import MockerFixture
from requests.exceptions import HTTPError
import pytest

def test_http_client_no_retry_on_401(mocker : MockerFixture, http_client):

    response = mocker.Mock()
    response.raise_for_status.side_effect = HTTPError(response=mocker.Mock(status_code=401))


    mocker.patch.object(
        http_client.session,
        "request",
        return_value=response,
    )

    with pytest.raises(HTTPError):
        http_client.get("/user")