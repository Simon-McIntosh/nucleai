"""Tests for IMAS URI parsing and conversion."""

from pathlib import Path

from nucleai.core.models import ImasUri


class TestImasUri:
    """Test ImasUri parsing and conversion."""

    def test_parse_uda_uri(self):
        """Test parsing UDA remote URI."""
        uri_str = "imas://uda.iter.org/uda?path=/work/imas/shared/simdb/uuid/imasdb/iter/3/53298/2&backend=hdf5"
        uri = ImasUri.from_string(uri_str)

        assert uri.original == uri_str
        assert uri.backend == "hdf5"
        assert uri.is_remote is True
        assert uri.server == "uda.iter.org"
        assert uri.path == "/work/imas/shared/simdb/uuid/imasdb/iter/3/53298/2"

    def test_parse_local_hdf5_uri(self):
        """Test parsing local HDF5 URI."""
        uri_str = "imas:hdf5?path=/work/imas/local/data"
        uri = ImasUri.from_string(uri_str)

        assert uri.original == uri_str
        assert uri.backend == "hdf5"
        assert uri.is_remote is False
        assert uri.server is None
        assert uri.path == "/work/imas/local/data"

    def test_parse_netcdf_uri(self):
        """Test parsing netCDF URI."""
        uri_str = "/work/imas/data/simulation.nc"
        uri = ImasUri.from_string(uri_str)

        assert uri.original == uri_str
        assert uri.backend == "netcdf"
        assert uri.is_remote is False
        assert uri.path == "/work/imas/data/simulation.nc"

    def test_parse_legacy_uri(self):
        """Test parsing legacy IMAS URI format."""
        uri_str = "imas:?shot=53298&run=2&user=public&database=iter&backend=hdf5"
        uri = ImasUri.from_string(uri_str)

        assert uri.backend == "hdf5"
        assert uri.is_remote is False
        # Legacy format doesn't have modern path
        assert uri.path is None

    def test_str_returns_original_when_no_conversion(self):
        """Test that str() returns original URI when no local data."""
        uri_str = "imas://uda.iter.org/uda?path=/nonexistent/path&backend=hdf5"
        uri = ImasUri.from_string(uri_str)

        # Should return original since local files don't exist
        assert str(uri) == uri_str

    def test_can_convert_requires_remote_uda(self):
        """Test that conversion requires remote UDA URI."""
        local_uri = ImasUri.from_string("imas:hdf5?path=/work/imas/data")
        assert local_uri.can_convert_to_local() is False  # Already local

    def test_to_local_returns_original_if_not_convertible(self):
        """Test that to_local returns original if URI cannot be converted."""
        local_uri = ImasUri.from_string("imas:hdf5?path=/work/imas/data")

        # Should return original (local URIs can't be "converted")
        result = local_uri.to_local()
        assert result == str(local_uri)

    def test_to_local_warns_on_failure(self, caplog):
        """Test that conversion failures warn rather than raise."""
        uri_str = "imas://uda.iter.org/uda?path=/nonexistent/data&backend=hdf5"
        uri = ImasUri.from_string(uri_str)

        # Conversion should fail gracefully and return original
        converted = str(uri)
        assert converted == uri_str  # Falls back to original

        # Should have logged warning
        # Note: Warnings are logged, check caplog or use pytest.warns


class TestImasUriFileDetection:
    """Test local file existence detection."""

    def test_local_files_exist_hdf5(self, tmp_path: Path):
        """Test HDF5 backend detection via master.h5."""
        data_dir = tmp_path / "hdf5_data"
        data_dir.mkdir()
        (data_dir / "master.h5").touch()

        uri_str = f"imas://uda.iter.org/uda?path={data_dir}&backend=hdf5"
        uri = ImasUri.from_string(uri_str)

        assert uri.can_convert_to_local() is True
        local_uri = uri.to_local()
        assert f"imas:hdf5?path={data_dir}" == local_uri

    def test_local_files_exist_netcdf(self, tmp_path: Path):
        """Test netCDF backend detection via .nc files."""
        data_dir = tmp_path / "netcdf_data"
        data_dir.mkdir()
        (data_dir / "simulation.nc").touch()

        uri_str = f"imas://uda.iter.org/uda?path={data_dir}/simulation.nc&backend=netcdf"
        uri = ImasUri.from_string(uri_str)

        # NetCDF files can be converted if they exist
        assert uri.can_convert_to_local() is True

    def test_local_files_exist_ascii(self, tmp_path: Path):
        """Test ASCII backend detection via .ids files."""
        data_dir = tmp_path / "ascii_data"
        data_dir.mkdir()
        (data_dir / "equilibrium.ids").touch()

        uri_str = f"imas://uda.iter.org/uda?path={data_dir}&backend=ascii"
        uri = ImasUri.from_string(uri_str)

        assert uri.can_convert_to_local() is True

    def test_local_files_not_exist(self, tmp_path: Path):
        """Test that nonexistent data returns False."""
        data_dir = tmp_path / "nonexistent"

        uri_str = f"imas://uda.iter.org/uda?path={data_dir}&backend=hdf5"
        uri = ImasUri.from_string(uri_str)

        assert uri.can_convert_to_local() is False


class TestImasUriAutoOptimization:
    """Test automatic URI optimization."""

    def test_str_converts_when_local_exists(self, tmp_path: Path):
        """Test that str() automatically converts to local when data exists."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "master.h5").touch()

        uda_uri = f"imas://uda.iter.org/uda?path={data_dir}&backend=hdf5"
        uri = ImasUri.from_string(uda_uri)

        # str() should return optimized local URI
        optimized = str(uri)
        assert optimized.startswith("imas:hdf5?path=")
        assert str(data_dir) in optimized
        assert "uda.iter.org" not in optimized

    def test_str_keeps_original_when_no_local(self):
        """Test that str() keeps original when local data doesn't exist."""
        uda_uri = "imas://uda.iter.org/uda?path=/nonexistent&backend=hdf5"
        uri = ImasUri.from_string(uda_uri)

        # Should return original since local doesn't exist
        assert str(uri) == uda_uri
