__all__ = ["generate_and_record"]


def __getattr__(name: str) -> object:
    if name == "generate_and_record":
        from deliverybrief.services.report_workflow import generate_and_record

        return generate_and_record
    raise AttributeError(name)
