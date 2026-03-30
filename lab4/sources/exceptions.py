class UniversityError(Exception):
    pass


class ResourceError(UniversityError):
    pass


class EnrollmentError(UniversityError):
    pass


class StateError(UniversityError):
    pass


class StorageError(UniversityError):
    pass
