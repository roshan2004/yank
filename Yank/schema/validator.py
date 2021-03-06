import os
import logging
import cerberus
import simtk.unit as unit

from datetime import date
from openmmtools.utils import typename
from collections.abc import Mapping, Sequence

logger = logging.getLogger(__name__)


class YANKCerberusValidator(cerberus.Validator):
    """
    Custom cerberus.Validator class for YANK extending the Validator to include all the methods needed
    by YANK
    """

    # ====================================================
    # DEFAULT SETTERS
    # ====================================================

    def _normalize_default_setter_no_parameters(self, document):
        return dict(parameters=list())

    # ====================================================
    # DATA COERCION
    # ====================================================

    def _normalize_coerce_single_str_to_list(self, value):
        """Cast a single string to a list of string"""
        return [value] if isinstance(value, str) else value

    # ====================================================
    # DATA VALIDATORS
    # ====================================================

    def _validator_file_exists(self, field, filepath):
        """Assert that the file is in fact, a file!"""
        if not os.path.isfile(filepath):
            self._error(field, 'File path {} does not exist.'.format(filepath))

    def _validator_directory_exists(self, field, directory_path):
        """Assert that the file is in fact, a file!"""
        if not os.path.isdir(directory_path):
            self._error(field, 'Directory {} does not exist.'.format(directory_path))

    def _validator_is_peptide(self, field, filepath):
        """Input file is a peptide."""
        extension = os.path.splitext(filepath)[1]
        if extension != '.pdb':
            self._error(field, "Not a .pdb file")

    def _validator_is_small_molecule(self, field, filepath):
        """Input file is a small molecule."""
        file_formats = frozenset(['mol2', 'sdf', 'smiles', 'csv'])
        extension = os.path.splitext(filepath)[1][1:]
        if extension not in file_formats:
            self._error(field, 'File is not one of {}'.format(file_formats))

    def _validator_positive_int_list(self, field, value):
        for p in value:
            if not isinstance(p, int) or not p >= 0:
                self._error(field, "{} of must be a positive integer!".format(p))

    def _validator_int_or_all_string(self, field, value):
        if value != 'all' and not isinstance(value, int):
            self._error(field, "{} must be an int or the string 'all'".format(value))

    def _validator_supported_system_files(self, field, file_paths):
        """Ensure the input system files are supported."""
        # Obtain the extension of the system files.
        file_extensions = {os.path.splitext(file_path)[1][1:] for file_path in file_paths}

        # Find a match for the extensions.
        expected_extensions = [
            ('amber', {'inpcrd', 'prmtop'}),
            ('amber', {'rst7', 'prmtop'}),
            ('gromacs', {'gro', 'top'}),
            ('openmm', {'pdb', 'xml'})
        ]
        file_extension_type = None
        for extension_type, valid_extensions in expected_extensions:
            if file_extensions == valid_extensions:
                file_extension_type = extension_type
                break

        # Verify we found a match.
        if file_extension_type is None:
            self._error(field, '{} must have file extensions matching one of the '
                               'following types: {}'.format(field, expected_extensions))
            return

        logger.debug('Correctly recognized {}files ({}) as {} '
                     'files'.format(field, file_paths, file_extension_type))

    # ====================================================
    # DATA TYPES
    # ====================================================

    def _validate_type_quantity(self, value):
        if isinstance(value, unit.Quantity):
            return True


# ====================================================
# UTILITY FUNCTIONS
# ====================================================

def generate_unknown_type_validator(a_type):
    """
    Helper function to :func:`type_to_cerberus_map` to convert unknown types into a validator

    Parameters
    ----------
    a_type : type
        Any valid type, although this works for any type, its preferred to let :func:`type_to_cerberus_map`
        to invoke this method

    Returns
    -------
    validator_map : dict
        Map dictionary of form ``{'validator': <function>}`` where ``'validator'`` is literal and
        ``<function>`` is a validator function of type checker.
    """
    def nonstandard_type_validator(field, value, error):
        if type(value) is not a_type:
            error(field, 'Must be of type {}'.format(typename(a_type)))
    validator_dict = {'validator': nonstandard_type_validator}
    return validator_dict


def type_to_cerberus_map(a_type):
    """
    Convert a provided type to a valid Cerberus internal type dict.

    Parameters
    ----------
    a_type : type
        Type you want the converter to built-in Cerberus strings

    Returns
    -------
    type_map : dict
        Type map dictionary of form ``{'type': 'TYPE'}`` where ``'type'`` is literal and ``TYPE`` is the mapped
        type in Cerberus

        OR

         Map dictionary of form ``{'validator': <function>}`` where ``'validator'`` is literal and
        ``<function>`` is a validator function of type checker for non-standard

    Raises
    ------
    YANKCerberusUtilsError
        When the type has no known map
    """
    known_types = {bool: 'boolean',
                   bytes: 'binary',
                   bytearray: 'binary',
                   date: 'date',
                   Mapping: 'dict',
                   dict: 'dict',
                   float: 'float',
                   int: 'integer',
                   tuple: 'list',
                   list: 'list',
                   Sequence: 'list',
                   str: 'string',
                   set: 'set'}
    try:
        type_map = {'type': known_types[a_type]}
    except KeyError:
        type_map = generate_unknown_type_validator(a_type)
    return type_map
