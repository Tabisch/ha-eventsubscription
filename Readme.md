# Event Subscribtion


Automation Template for Subscribing a User that has pressed a button

alias: register
description: ""
trigger:
  - platform: state
    entity_id:
      - input_button.button
condition: []
action:
  - service: eventsubscription.register
    data:
      eventname: test
      completemessage: complete
      registermessage: register
      deleteaftercompletion: false
      targetText: >-
        {% for state in states.person -%}{% if state.attributes.user_id ==
        trigger.to_state.context.user_id %}{{state.attributes.friendly_name}}{%
        endif %}{%- endfor %}
mode: single