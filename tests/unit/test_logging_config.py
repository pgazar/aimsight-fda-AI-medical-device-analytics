import logging

from aimsight.logging_config import configure_logging, get_logger


def test_get_logger_returns_a_logger_with_the_requested_name():
    logger = get_logger("aimsight.transform.clean_ai_devices")
    assert logger.name == "aimsight.transform.clean_ai_devices"


def test_configure_logging_does_not_attach_duplicate_handlers():
    # We can't assert an absolute handler count: pytest's own logging
    # plugin attaches handlers to the root logger too (for test-output
    # capturing), so the total varies by environment. What we can assert
    # is that OUR handler only gets attached once — repeated calls must
    # not keep adding to whatever count already existed.
    configure_logging()
    handler_count_after_first_call = len(logging.getLogger().handlers)

    configure_logging()
    configure_logging()

    assert len(logging.getLogger().handlers) == handler_count_after_first_call


def test_info_message_is_emitted_and_readable(caplog):
    logger = get_logger("aimsight.test")
    with caplog.at_level(logging.INFO, logger="aimsight.test"):
        logger.info("pipeline run started")
    assert "pipeline run started" in caplog.text
    assert caplog.records[0].levelname == "INFO"
