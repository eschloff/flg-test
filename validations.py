import json


def cloze_blob(template, responses, validations, keyboards=None, options=None,
               alternates=None, alt_validations=None, alt_options=None):
    """

    :param template:
    :param responses:
    :param validations:
    :param keyboards:
    :param options:
    :param alternates:
    :param alt_validations:
    :param alt_options:
    :return:
    """

    if not options:
        options = {"ignoreText": True, "decimalPlaces": 10}
    if not keyboards:
        keyboards = ["basic", "qwerty"]

    value = []
    for (response, validation) in zip(responses, validations):
        value.append([{"method": validation, "value": response, "options": options}])
    valid_response = {"score": 1, "value": value}

    if alternates:
        if not alt_validations:
            alt_validations = validations
        if not alt_options:
            alt_options = options

        alt_response = []
        for r in alternates:
            value = []
            for (response, validation) in zip(r, alt_validations):
                value.append([{"method": validation, "value": response, "options": alt_options}])
            alt_response.append({"score": 1, "value": value})

    else:
        alt_response = []

    validation = {"scoring_type": "exactMatch", "valid_response": valid_response, "alt_responses": alt_response}

    blob = {"type": "clozeformula",
            "is_math": True,
            "ui_style": {"type": "block-on-focus-keyboard"},
            "template": template,
            "response_containers": [],
            "symbols": keyboards,
            "validation": validation}

    return json.dumps(blob)


def lea_blob(template, response, validation, keyboards=None, options=None,
             alternates=None, alt_validations=None, alt_options=None,
             blacklist=None, blacklist_validations=None):
    """

    :param template:
    :param response:
    :param validation:
    :param keyboards:
    :param options:
    :param alternates:
    :param alt_validations:
    :param alt_options:
    :return:
    """

    if not options:
        options = {"ignoreText": True, "decimalPlaces": 10}
    if not keyboards:
        keyboards = ["basic", "qwerty"]

    value = [{"method": validation, "value": response, "options": options}]
    if blacklist and not blacklist_validations:

        blacklist_options = {"ignoreOrder": True, "ignoreCoefficientOne": True, "inverseResult": True}

        for response in blacklist:
            value.append({"method": "equivLiteral", "value": response, "options": blacklist_options})

    valid_response = {"score": 1, "value": value}

    alt_response = []
    if alternates:
        if not alt_validations:
            alt_validations = [validation] * len(alternates)
        if not alt_options:
            alt_options = options

        for (response, validation) in zip(alternates, alt_validations):
            value = [{"method": validation, "value": response, "options": alt_options}]
            alt_response.append({"score": 1, "value": value})

    if blacklist and blacklist_validations:
        if not blacklist_validations:
            blacklist_validations = ["equivLiteral"] * len(blacklist)
        blacklist_options = options

        for (response, validation) in zip(blacklist, blacklist_validations):
            value = [{"method": validation, "value": response, "options": blacklist_options}]
            alt_response.append({"score": 0, "value": value})

    validation = {"scoring_type": "exactMatch", "valid_response": valid_response, "alt_responses": alt_response}

    blob = {"type": "formulaV2",
            "is_math": True,
            "ui_style": {"type": "block-on-focus-keyboard"},
            "template": template,
            "response_containers": [],
            "symbols": keyboards,
            "validation": validation}

    return json.dumps(blob)