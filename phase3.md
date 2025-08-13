# OpenAI Agent sdk レスポンスの正しいパース

print関数の出力

```
INFO:     127.0.0.1:53798 - "POST /api/chat/stream/6f200eb2-10ab-4a2f-86a4-d385756a0520 HTTP/1.1" 200 OK
[{'role': 'user', 'content': 'お疲れ様です'}]
Event: AgentUpdatedStreamEvent(new_agent=Agent(name='ChatAssistant', handoff_description=None, tools=[FunctionTool(name='get_current_time', description='現在の時刻を取得します。', params_json_schema={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f959940>, strict_json_schema=True, is_enabled=True), FunctionTool(name='calculate', description='数式を計算します。安全な数式のみサポートします。', params_json_schema={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a020>, strict_json_schema=True, is_enabled=True), FunctionTool(name='web_search', description='Web検索を実行します（Mock版）。', params_json_schema={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a160>, strict_json_schema=True, is_enabled=True)], mcp_servers=[], mcp_config={}, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', prompt=None, handoffs=[], model='gpt-4o-mini', model_settings=ModelSettings(temperature=0.7, top_p=None, frequency_penalty=None, presence_penalty=None, tool_choice=None, parallel_tool_calls=None, truncation=None, max_tokens=1024, reasoning=None, metadata=None, store=None, include_usage=None, response_include=None, extra_query=None, extra_body=None, extra_headers=None, extra_args=None), input_guardrails=[], output_guardrails=[], output_type=None, hooks=None, tool_use_behavior='run_llm_again', reset_tool_choice=True), type='agent_updated_stream_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseCreatedEvent(response=Response(id='resp_689459c07eec8192912aa5b8e610f0990ae04b40055a4027', created_at=1754552768.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='auto', status='in_progress', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=None, user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=0, type='response.created'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseInProgressEvent(response=Response(id='resp_689459c07eec8192912aa5b8e610f0990ae04b40055a4027', created_at=1754552768.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='auto', status='in_progress', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=None, user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=1, type='response.in_progress'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseOutputItemAddedEvent(item=ResponseOutputMessage(id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', content=[], role='assistant', status='in_progress', type='message'), output_index=0, sequence_number=2, type='response.output_item.added'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseContentPartAddedEvent(content_index=0, item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, part=ResponseOutputText(annotations=[], text='', type='output_text', logprobs=[]), sequence_number=3, type='response.content_part.added'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='お', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=4, type='response.output_text.delta', logprobs=[], obfuscation='50m6gM7Z1NqOiNa'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='疲', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=5, type='response.output_text.delta', logprobs=[], obfuscation='qiRdDTOwUzFpJGP'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='れ', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=6, type='response.output_text.delta', logprobs=[], obfuscation='9x8qQw4aYlFCNJd'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='様', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=7, type='response.output_text.delta', logprobs=[], obfuscation='JURM87uc7lT4uT2'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='です', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=8, type='response.output_text.delta', logprobs=[], obfuscation='QBwAr5qRfE3Jpz'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='！', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=9, type='response.output_text.delta', logprobs=[], obfuscation='RwaQs1xLQhG8yjd'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='今日は', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=10, type='response.output_text.delta', logprobs=[], obfuscation='iZk5p3dUXiHCV'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='ど', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=11, type='response.output_text.delta', logprobs=[], obfuscation='MLQ0vtAmZFZuxxC'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='の', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=12, type='response.output_text.delta', logprobs=[], obfuscation='NDpf1fHeJvpmDYY'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='よう', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=13, type='response.output_text.delta', logprobs=[], obfuscation='2pLXiNZsg4R2dG'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='な', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=14, type='response.output_text.delta', logprobs=[], obfuscation='rhp8D02eLr5JoiM'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='こと', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=15, type='response.output_text.delta', logprobs=[], obfuscation='5l0fdEvZAlh9hJ'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='を', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=16, type='response.output_text.delta', logprobs=[], obfuscation='nbrQa7xoTyUt09w'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='お', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=17, type='response.output_text.delta', logprobs=[], obfuscation='wHGbhddxgIdzTPu'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='手', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=18, type='response.output_text.delta', logprobs=[], obfuscation='1UBKtXYmlyR7BYd'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='伝', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=19, type='response.output_text.delta', logprobs=[], obfuscation='jXHbsDQKbeeBnvJ'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='い', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=20, type='response.output_text.delta', logprobs=[], obfuscation='dJEOqGUoBO23jSv'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='できます', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=21, type='response.output_text.delta', logprobs=[], obfuscation='E35JvBnZKgDl'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='か', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=22, type='response.output_text.delta', logprobs=[], obfuscation='nmzFhvTTc5hcyrR'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='？', item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=23, type='response.output_text.delta', logprobs=[], obfuscation='o2QkEqqqtxELV29'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDoneEvent(content_index=0, item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, sequence_number=24, text='お疲れ様です！今日はどのようなことをお手伝いできますか？', type='response.output_text.done', logprobs=[]), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseContentPartDoneEvent(content_index=0, item_id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', output_index=0, part=ResponseOutputText(annotations=[], text='お疲れ様です！今日はどのようなことをお手伝いできますか？', type='output_text', logprobs=[]), sequence_number=25, type='response.content_part.done'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseOutputItemDoneEvent(item=ResponseOutputMessage(id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', content=[ResponseOutputText(annotations=[], text='お疲れ様です！今日はどのようなことをお手伝いできますか？', type='output_text', logprobs=[])], role='assistant', status='completed', type='message'), output_index=0, sequence_number=26, type='response.output_item.done'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseCompletedEvent(response=Response(id='resp_689459c07eec8192912aa5b8e610f0990ae04b40055a4027', created_at=1754552768.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[ResponseOutputMessage(id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', content=[ResponseOutputText(annotations=[], text='お疲れ様です！今日はどのようなことをお手伝いできますか？', type='output_text', logprobs=[])], role='assistant', status='completed', type='message')], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='default', status='completed', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=ResponseUsage(input_tokens=257, input_tokens_details=InputTokensDetails(cached_tokens=0), output_tokens=22, output_tokens_details=OutputTokensDetails(reasoning_tokens=0), total_tokens=279), user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=27, type='response.completed'), type='raw_response_event')¥n
----------
Event: RunItemStreamEvent(name='message_output_created', item=MessageOutputItem(agent=Agent(name='ChatAssistant', handoff_description=None, tools=[FunctionTool(name='get_current_time', description='現在の時刻を取得します。', params_json_schema={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f959940>, strict_json_schema=True, is_enabled=True), FunctionTool(name='calculate', description='数式を計算します。安全な数式のみサポートします。', params_json_schema={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a020>, strict_json_schema=True, is_enabled=True), FunctionTool(name='web_search', description='Web検索を実行します（Mock版）。', params_json_schema={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a160>, strict_json_schema=True, is_enabled=True)], mcp_servers=[], mcp_config={}, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', prompt=None, handoffs=[], model='gpt-4o-mini', model_settings=ModelSettings(temperature=0.7, top_p=None, frequency_penalty=None, presence_penalty=None, tool_choice=None, parallel_tool_calls=None, truncation=None, max_tokens=1024, reasoning=None, metadata=None, store=None, include_usage=None, response_include=None, extra_query=None, extra_body=None, extra_headers=None, extra_args=None), input_guardrails=[], output_guardrails=[], output_type=None, hooks=None, tool_use_behavior='run_llm_again', reset_tool_choice=True), raw_item=ResponseOutputMessage(id='msg_689459c0edd88192867db826fe73a4ab0ae04b40055a4027', content=[ResponseOutputText(annotations=[], text='お疲れ様です！今日はどのようなことをお手伝いできますか？', type='output_text', logprobs=[])], role='assistant', status='completed', type='message'), type='message_output_item'), type='run_item_stream_event')¥n
----------
INFO:     127.0.0.1:53802 - "GET /api/conversations HTTP/1.1" 200 OK
INFO:     127.0.0.1:53807 - "POST /api/chat/stream/6f200eb2-10ab-4a2f-86a4-d385756a0520 HTTP/1.1" 200 OK
[{'role': 'user', 'content': 'お疲れ様です'}, {'role': 'assistant', 'content': 'お疲れ様です！今日はどのようなことをお手伝いできますか？'}, {'role': 'user', 'content': '今何時ですか？'}]
Event: AgentUpdatedStreamEvent(new_agent=Agent(name='ChatAssistant', handoff_description=None, tools=[FunctionTool(name='get_current_time', description='現在の時刻を取得します。', params_json_schema={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f959940>, strict_json_schema=True, is_enabled=True), FunctionTool(name='calculate', description='数式を計算します。安全な数式のみサポートします。', params_json_schema={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a020>, strict_json_schema=True, is_enabled=True), FunctionTool(name='web_search', description='Web検索を実行します（Mock版）。', params_json_schema={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a160>, strict_json_schema=True, is_enabled=True)], mcp_servers=[], mcp_config={}, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', prompt=None, handoffs=[], model='gpt-4o-mini', model_settings=ModelSettings(temperature=0.7, top_p=None, frequency_penalty=None, presence_penalty=None, tool_choice=None, parallel_tool_calls=None, truncation=None, max_tokens=1024, reasoning=None, metadata=None, store=None, include_usage=None, response_include=None, extra_query=None, extra_body=None, extra_headers=None, extra_args=None), input_guardrails=[], output_guardrails=[], output_type=None, hooks=None, tool_use_behavior='run_llm_again', reset_tool_choice=True), type='agent_updated_stream_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseCreatedEvent(response=Response(id='resp_689459c9081c819ca947bf0e03b66c860638fadc601bd529', created_at=1754552777.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='auto', status='in_progress', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=None, user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=0, type='response.created'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseInProgressEvent(response=Response(id='resp_689459c9081c819ca947bf0e03b66c860638fadc601bd529', created_at=1754552777.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='auto', status='in_progress', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=None, user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=1, type='response.in_progress'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseOutputItemAddedEvent(item=ResponseFunctionToolCall(arguments='', call_id='call_9wl1PbtYI3EWmMIFWl6oI1g1', name='get_current_time', type='function_call', id='fc_689459c9ff90819cb1f3e9a312e2fe7b0638fadc601bd529', status='in_progress'), output_index=0, sequence_number=2, type='response.output_item.added'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseFunctionCallArgumentsDeltaEvent(delta='{}', item_id='fc_689459c9ff90819cb1f3e9a312e2fe7b0638fadc601bd529', output_index=0, sequence_number=3, type='response.function_call_arguments.delta', obfuscation='wFGp7vc6bdsOtf'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseFunctionCallArgumentsDoneEvent(arguments='{}', item_id='fc_689459c9ff90819cb1f3e9a312e2fe7b0638fadc601bd529', output_index=0, sequence_number=4, type='response.function_call_arguments.done'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseOutputItemDoneEvent(item=ResponseFunctionToolCall(arguments='{}', call_id='call_9wl1PbtYI3EWmMIFWl6oI1g1', name='get_current_time', type='function_call', id='fc_689459c9ff90819cb1f3e9a312e2fe7b0638fadc601bd529', status='completed'), output_index=0, sequence_number=5, type='response.output_item.done'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseCompletedEvent(response=Response(id='resp_689459c9081c819ca947bf0e03b66c860638fadc601bd529', created_at=1754552777.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[ResponseFunctionToolCall(arguments='{}', call_id='call_9wl1PbtYI3EWmMIFWl6oI1g1', name='get_current_time', type='function_call', id='fc_689459c9ff90819cb1f3e9a312e2fe7b0638fadc601bd529', status='completed')], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='default', status='completed', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=ResponseUsage(input_tokens=291, input_tokens_details=InputTokensDetails(cached_tokens=0), output_tokens=12, output_tokens_details=OutputTokensDetails(reasoning_tokens=0), total_tokens=303), user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=6, type='response.completed'), type='raw_response_event')¥n
----------
Event: RunItemStreamEvent(name='tool_called', item=ToolCallItem(agent=Agent(name='ChatAssistant', handoff_description=None, tools=[FunctionTool(name='get_current_time', description='現在の時刻を取得します。', params_json_schema={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f959940>, strict_json_schema=True, is_enabled=True), FunctionTool(name='calculate', description='数式を計算します。安全な数式のみサポートします。', params_json_schema={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a020>, strict_json_schema=True, is_enabled=True), FunctionTool(name='web_search', description='Web検索を実行します（Mock版）。', params_json_schema={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a160>, strict_json_schema=True, is_enabled=True)], mcp_servers=[], mcp_config={}, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', prompt=None, handoffs=[], model='gpt-4o-mini', model_settings=ModelSettings(temperature=0.7, top_p=None, frequency_penalty=None, presence_penalty=None, tool_choice=None, parallel_tool_calls=None, truncation=None, max_tokens=1024, reasoning=None, metadata=None, store=None, include_usage=None, response_include=None, extra_query=None, extra_body=None, extra_headers=None, extra_args=None), input_guardrails=[], output_guardrails=[], output_type=None, hooks=None, tool_use_behavior='run_llm_again', reset_tool_choice=True), raw_item=ResponseFunctionToolCall(arguments='{}', call_id='call_9wl1PbtYI3EWmMIFWl6oI1g1', name='get_current_time', type='function_call', id='fc_689459c9ff90819cb1f3e9a312e2fe7b0638fadc601bd529', status='completed'), type='tool_call_item'), type='run_item_stream_event')¥n
----------
Event: RunItemStreamEvent(name='tool_output', item=ToolCallOutputItem(agent=Agent(name='ChatAssistant', handoff_description=None, tools=[FunctionTool(name='get_current_time', description='現在の時刻を取得します。', params_json_schema={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f959940>, strict_json_schema=True, is_enabled=True), FunctionTool(name='calculate', description='数式を計算します。安全な数式のみサポートします。', params_json_schema={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a020>, strict_json_schema=True, is_enabled=True), FunctionTool(name='web_search', description='Web検索を実行します（Mock版）。', params_json_schema={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a160>, strict_json_schema=True, is_enabled=True)], mcp_servers=[], mcp_config={}, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', prompt=None, handoffs=[], model='gpt-4o-mini', model_settings=ModelSettings(temperature=0.7, top_p=None, frequency_penalty=None, presence_penalty=None, tool_choice=None, parallel_tool_calls=None, truncation=None, max_tokens=1024, reasoning=None, metadata=None, store=None, include_usage=None, response_include=None, extra_query=None, extra_body=None, extra_headers=None, extra_args=None), input_guardrails=[], output_guardrails=[], output_type=None, hooks=None, tool_use_behavior='run_llm_again', reset_tool_choice=True), raw_item={'call_id': 'call_9wl1PbtYI3EWmMIFWl6oI1g1', 'output': '2025-08-07 07:46:18 UTC', 'type': 'function_call_output'}, output='2025-08-07 07:46:18 UTC', type='tool_call_output_item'), type='run_item_stream_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseCreatedEvent(response=Response(id='resp_689459ca5ef8819ca4837d83694e7f930638fadc601bd529', created_at=1754552778.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='auto', status='in_progress', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=None, user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=0, type='response.created'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseInProgressEvent(response=Response(id='resp_689459ca5ef8819ca4837d83694e7f930638fadc601bd529', created_at=1754552778.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='auto', status='in_progress', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=None, user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=1, type='response.in_progress'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseOutputItemAddedEvent(item=ResponseOutputMessage(id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', content=[], role='assistant', status='in_progress', type='message'), output_index=0, sequence_number=2, type='response.output_item.added'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseContentPartAddedEvent(content_index=0, item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, part=ResponseOutputText(annotations=[], text='', type='output_text', logprobs=[]), sequence_number=3, type='response.content_part.added'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='現在', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=4, type='response.output_text.delta', logprobs=[], obfuscation='LUTOi6cQbmciqD'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='の', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=5, type='response.output_text.delta', logprobs=[], obfuscation='rjshG4NEEAW4zK1'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='時', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=6, type='response.output_text.delta', logprobs=[], obfuscation='RMtUX2Wu6nsBzY7'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='刻', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=7, type='response.output_text.delta', logprobs=[], obfuscation='1cdnhlKuWcpvevp'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='は', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=8, type='response.output_text.delta', logprobs=[], obfuscation='h5E7nQUEIJjuN3B'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='、', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=9, type='response.output_text.delta', logprobs=[], obfuscation='OtwMA5yZ7rcVeI0'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='UTC', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=10, type='response.output_text.delta', logprobs=[], obfuscation='wgxwSLpKh7iWh'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='で', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=11, type='response.output_text.delta', logprobs=[], obfuscation='B5qGOR77vYyMER6'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='202', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=12, type='response.output_text.delta', logprobs=[], obfuscation='X3zN4N9Qxpovu'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='5', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=13, type='response.output_text.delta', logprobs=[], obfuscation='ewDZBbPhDuBUllF'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='年', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=14, type='response.output_text.delta', logprobs=[], obfuscation='sRKZyB5fxcWd0q4'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='8', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=15, type='response.output_text.delta', logprobs=[], obfuscation='lZDPJ4Dr2zI81vi'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='月', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=16, type='response.output_text.delta', logprobs=[], obfuscation='0fFyPpIk6tScDUF'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='7', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=17, type='response.output_text.delta', logprobs=[], obfuscation='hgSc4L2ecd3YXBT'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='日', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=18, type='response.output_text.delta', logprobs=[], obfuscation='SWPUwILJiOL1j5R'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='07', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=19, type='response.output_text.delta', logprobs=[], obfuscation='qOwwxMrdfu4RbB'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta=':', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=20, type='response.output_text.delta', logprobs=[], obfuscation='XSxGmXLKDTwL8GB'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='46', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=21, type='response.output_text.delta', logprobs=[], obfuscation='ONeOIi83ZxEc39'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='です', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=22, type='response.output_text.delta', logprobs=[], obfuscation='q2ef5erT5XpTCy'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='。', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=23, type='response.output_text.delta', logprobs=[], obfuscation='DaiqQYIKXabxH8d'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='お', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=24, type='response.output_text.delta', logprobs=[], obfuscation='FLEbWYCv8Md8oGI'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='住', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=25, type='response.output_text.delta', logprobs=[], obfuscation='RKNbETRZhLdfOP3'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='ま', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=26, type='response.output_text.delta', logprobs=[], obfuscation='rpJ5EVf5lwCd8Fu'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='い', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=27, type='response.output_text.delta', logprobs=[], obfuscation='pWTJF2VpmDou7C6'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='の', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=28, type='response.output_text.delta', logprobs=[], obfuscation='fWi4pKhKwTCL4dM'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='地域', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=29, type='response.output_text.delta', logprobs=[], obfuscation='PQ4Pm0uZHonEJ4'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='の', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=30, type='response.output_text.delta', logprobs=[], obfuscation='PB0ug5QsbKXI32x'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='時間', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=31, type='response.output_text.delta', logprobs=[], obfuscation='55EqykQcOL6lNC'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='帯', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=32, type='response.output_text.delta', logprobs=[], obfuscation='XWVZWDpHE0A0v6w'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='に', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=33, type='response.output_text.delta', logprobs=[], obfuscation='c1EAyUDiO0lH8QJ'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='合わせ', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=34, type='response.output_text.delta', logprobs=[], obfuscation='OHdOsMoL6Lpq2'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='た', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=35, type='response.output_text.delta', logprobs=[], obfuscation='vG3rnUQJl269t3p'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='時', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=36, type='response.output_text.delta', logprobs=[], obfuscation='XJ6oCfR6jhGHvXG'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='刻', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=37, type='response.output_text.delta', logprobs=[], obfuscation='VnYTzI2qexWB2bu'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='が', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=38, type='response.output_text.delta', logprobs=[], obfuscation='u0FEGWAnRiw6gl8'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='必要', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=39, type='response.output_text.delta', logprobs=[], obfuscation='CogO0WbryEUN6e'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='で', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=40, type='response.output_text.delta', logprobs=[], obfuscation='fs7PijNGXyH18cS'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='あ', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=41, type='response.output_text.delta', logprobs=[], obfuscation='xLXhvE1CovBh6MH'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='れば', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=42, type='response.output_text.delta', logprobs=[], obfuscation='A0lBsYpPocbbhr'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='教', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=43, type='response.output_text.delta', logprobs=[], obfuscation='geuUWUgcRNNk816'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='えて', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=44, type='response.output_text.delta', logprobs=[], obfuscation='iivDdKWuY8ssbI'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='ください', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=45, type='response.output_text.delta', logprobs=[], obfuscation='1iVB2aHeTXnW'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDeltaEvent(content_index=0, delta='。', item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=46, type='response.output_text.delta', logprobs=[], obfuscation='ENivaGeAMJb4iBy'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseTextDoneEvent(content_index=0, item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, sequence_number=47, text='現在の時刻は、UTCで2025年8月7日07:46です。お住まいの地域の時間帯に合わせた時刻が必要であれば教えてください。', type='response.output_text.done', logprobs=[]), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseContentPartDoneEvent(content_index=0, item_id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', output_index=0, part=ResponseOutputText(annotations=[], text='現在の時刻は、UTCで2025年8月7日07:46です。お住まいの地域の時間帯に合わせた時刻が必要であれば教えてください。', type='output_text', logprobs=[]), sequence_number=48, type='response.content_part.done'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseOutputItemDoneEvent(item=ResponseOutputMessage(id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', content=[ResponseOutputText(annotations=[], text='現在の時刻は、UTCで2025年8月7日07:46です。お住まいの地域の時間帯に合わせた時刻が必要であれば教えてください。', type='output_text', logprobs=[])], role='assistant', status='completed', type='message'), output_index=0, sequence_number=49, type='response.output_item.done'), type='raw_response_event')¥n
----------
Event: RawResponsesStreamEvent(data=ResponseCompletedEvent(response=Response(id='resp_689459ca5ef8819ca4837d83694e7f930638fadc601bd529', created_at=1754552778.0, error=None, incomplete_details=None, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', metadata={}, model='gpt-4o-mini-2024-07-18', object='response', output=[ResponseOutputMessage(id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', content=[ResponseOutputText(annotations=[], text='現在の時刻は、UTCで2025年8月7日07:46です。お住まいの地域の時間帯に合わせた時刻が必要であれば教えてください。', type='output_text', logprobs=[])], role='assistant', status='completed', type='message')], parallel_tool_calls=True, temperature=0.7, tool_choice='auto', tools=[FunctionTool(name='get_current_time', parameters={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, strict=True, type='function', description='現在の時刻を取得します。'), FunctionTool(name='calculate', parameters={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='数式を計算します。安全な数式のみサポートします。'), FunctionTool(name='web_search', parameters={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, strict=True, type='function', description='Web検索を実行します（Mock版）。')], top_p=1.0, background=False, max_output_tokens=1024, max_tool_calls=None, previous_response_id=None, prompt=None, reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='default', status='completed', text=ResponseTextConfig(format=ResponseFormatText(type='text')), top_logprobs=0, truncation='disabled', usage=ResponseUsage(input_tokens=325, input_tokens_details=InputTokensDetails(cached_tokens=0), output_tokens=45, output_tokens_details=OutputTokensDetails(reasoning_tokens=0), total_tokens=370), user=None, prompt_cache_key=None, safety_identifier=None, store=True), sequence_number=50, type='response.completed'), type='raw_response_event')¥n
----------
Event: RunItemStreamEvent(name='message_output_created', item=MessageOutputItem(agent=Agent(name='ChatAssistant', handoff_description=None, tools=[FunctionTool(name='get_current_time', description='現在の時刻を取得します。', params_json_schema={'properties': {}, 'title': 'get_current_time_args', 'type': 'object', 'additionalProperties': False, 'required': []}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f959940>, strict_json_schema=True, is_enabled=True), FunctionTool(name='calculate', description='数式を計算します。安全な数式のみサポートします。', params_json_schema={'properties': {'expression': {'description': '計算する数式（例: "2 + 3 * 4"）', 'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], 'title': 'calculate_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a020>, strict_json_schema=True, is_enabled=True), FunctionTool(name='web_search', description='Web検索を実行します（Mock版）。', params_json_schema={'properties': {'query': {'description': '検索クエリ', 'title': 'Query', 'type': 'string'}, 'max_results': {'default': 5, 'description': '最大結果数（デフォルト: 5）', 'title': 'Max Results', 'type': 'integer'}}, 'required': ['query', 'max_results'], 'title': 'web_search_args', 'type': 'object', 'additionalProperties': False}, on_invoke_tool=<function function_tool.<locals>._create_function_tool.<locals>._on_invoke_tool at 0x10f95a160>, strict_json_schema=True, is_enabled=True)], mcp_servers=[], mcp_config={}, instructions='あなたは親切で知識豊富なアシスタントです。\n            ユーザーの質問に正確かつ丁寧に答えてください。\n            必要に応じてツールを使用してください。\n            時刻の取得や計算が必要な場合は、適切なツールを使用してください。\n            回答は常にユーザーの言語で行ってください。', prompt=None, handoffs=[], model='gpt-4o-mini', model_settings=ModelSettings(temperature=0.7, top_p=None, frequency_penalty=None, presence_penalty=None, tool_choice=None, parallel_tool_calls=None, truncation=None, max_tokens=1024, reasoning=None, metadata=None, store=None, include_usage=None, response_include=None, extra_query=None, extra_body=None, extra_headers=None, extra_args=None), input_guardrails=[], output_guardrails=[], output_type=None, hooks=None, tool_use_behavior='run_llm_again', reset_tool_choice=True), raw_item=ResponseOutputMessage(id='msg_689459caeae0819ca4837db31d3e06be0638fadc601bd529', content=[ResponseOutputText(annotations=[], text='現在の時刻は、UTCで2025年8月7日07:46です。お住まいの地域の時間帯に合わせた時刻が必要であれば教えてください。', type='output_text', logprobs=[])], role='assistant', status='completed', type='message'), type='message_output_item'), type='run_item_stream_event')¥n
----------
INFO:     127.0.0.1:53812 - "GET /api/conversations HTTP/1.1" 200 OK

```


現状の実装


```python
# ---------- SSE ----------
@app.post("/api/chat/stream/{conversation_id}")
async def stream_chat(
    conversation_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    chat_agent: Agent = Depends(get_chat_agent),
):
    """SSEによるリアルタイムチャット"""

    async def generate_sse_stream():
        try:
            # 会話の取得または作成
            conv = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == current_user.id,
                )
                .first()
            )

            if not conv:
                conv = Conversation(id=conversation_id, user_id=current_user.id)
                db.add(conv)
                db.commit()


            # userメッセージはストリーミング前に必ず1回だけ保存
            user_msg = Message(
                conversation_id=conv.id, role="user", content=request.message
            )
            db.add(user_msg)
            db.commit()

            # API用メッセージ履歴を準備（toolメッセージは除外）
            api_messages = [
                {"role": m.role, "content": m.content}
                for m in conv.messages
                if should_include_message(m)
            ]
            print(api_messages)

            # ストリーミング開始
            assistant_content = ""
            assistant_id = generate_unique_id()
            tool_tracking = {}  # ツール実行追跡: call_id -> {tool_name, tool_call_id}
            sent_tool_messages = []  # SSE送信したrole:toolメッセージを保存（DB保存用）

            # Agents SDK でストリーミング実行（依存性注入されたagent使用）
            result = Runner.run_streamed(chat_agent, api_messages)
            async for event in result.stream_events():
                print(f"Event: {event}¥n")
                print(f"----------")
                # ツールイベント検出
                if hasattr(event, "item") and hasattr(event.item, "type"):

                    if event.item.type == "tool_call_item":
                        # ツール呼び出し開始
                        raw_item = event.item.raw_item
                        tool_name = (
                            raw_item.get("name")
                            if hasattr(raw_item, "get")
                            else getattr(raw_item, "name", "unknown")
                        )
                        call_id = getattr(event.item, "id", generate_unique_id())

                        tool_tracking[call_id] = {
                            "tool_name": tool_name,
                            "tool_call_id": call_id
                        }

                    elif event.item.type == "tool_call_output_item":
                        # ツール実行完了
                        # call_idを複数の方法で取得を試行
                        call_id = (
                            getattr(event.item, "tool_call_id", None) or
                            getattr(event.item, "id", None) or
                            getattr(getattr(event.item, "raw_item", {}), "tool_call_id", None) or
                            "unknown_call"
                        )
                        output = getattr(event.item, "output", "")

                        # ツール名を特定（辞書からまたは別の方法で）
                        tool_name = ""
                        tool_info = None

                        # まず辞書から検索
                        if call_id in tool_tracking:
                            tool_info = tool_tracking[call_id]
                            tool_name = tool_info["tool_name"]
                        else:
                            # 辞書にない場合は、最初のエントリを使用（単一ツール実行の場合）
                            if len(tool_tracking) == 1:
                                first_key = next(iter(tool_tracking))
                                tool_info = tool_tracking[first_key]
                                tool_name = tool_info["tool_name"]
                                call_id = first_key  # 正しいIDに修正
                            else:
                                # 部分的なIDマッチングも試行
                                for tid, tinfo in tool_tracking.items():
                                    if tid in call_id or call_id in tid:
                                        tool_info = tinfo
                                        tool_name = tinfo["tool_name"]
                                        call_id = tid  # 正しいIDに修正
                                        break

                        if tool_info:
                            # phase1.md仕様のrole: toolイベントを送信
                            tool_content_dict = {
                                "tool_call_id": call_id,
                                "tool_name": tool_name,
                                "output": output,
                                "status": "success"
                            }

                            tool_event = {
                                "role": "tool",
                                "content": json.dumps(tool_content_dict, ensure_ascii=False),
                                "id": call_id,
                                "timestamp": datetime.now(UTC).isoformat()
                            }
                            yield f"data: {json.dumps(tool_event, ensure_ascii=False)}\n\n"

                            # DB保存用に情報を保存
                            sent_tool_messages.append({
                                "role": "tool",
                                "content": json.dumps(tool_content_dict, ensure_ascii=False)
                            })

                            # 完了したツールは辞書から削除
                            del tool_tracking[call_id]

                elif isinstance(event, RawResponsesStreamEvent):
                    if isinstance(event.data, ResponseTextDeltaEvent):
                        content = event.data.delta
                        assistant_content += content
                        content_event = {
                            "role": "assistant",
                            "content": content,
                            "id": assistant_id
                        }
                        yield f"data: {json.dumps(content_event, ensure_ascii=False)}\n\n"
                    elif isinstance(event.data, ResponseFunctionCallArgumentsDeltaEvent):
                        pass

            # メッセージ保存
            # SSE送信したツールメッセージを保存
            for tool_msg in sent_tool_messages:
                db_message = Message(
                    conversation_id=conv.id,
                    role=tool_msg["role"],
                    content=tool_msg["content"]
                )
                db.add(db_message)

            # 最終的なassistantメッセージを保存（assistant_contentがある場合のみ）
            if assistant_content.strip():
                db_message = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=assistant_content
                )
                db.add(db_message)


            # タイトル生成処理
            if not conv.title and len(conv.messages) > 0:
                first_user_msg = next(
                    (m for m in conv.messages if m.role == "user"), None
                )
                if first_user_msg:
                    conv.title = first_user_msg.content[:50] + (
                        "..." if len(first_user_msg.content) > 50 else ""
                    )

            conv.updated_at = datetime.now(UTC)
            db.commit()

            # ストリーミング完了
            done_event = {"id": assistant_id}
            yield f"done: {json.dumps(done_event, ensure_ascii=False)}\n"

        except Exception as e:
            # エラー送信
            error_event = {"error": f"エラーが発生しました: {str(e)}"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        finally:
            db.close()

    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization",
        },
    )
```