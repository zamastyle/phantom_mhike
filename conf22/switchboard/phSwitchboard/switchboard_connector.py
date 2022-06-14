import phantom.app as phantom
from phantom.action_result import ActionResult
import json
import requests
import datetime


class SwitchboardConnector(phantom.BaseConnector):

    is_polling_action = False

    def __init__(self):
        super(SwitchboardConnector, self).__init__()
        return
            
    def __print(self, value, is_debug):
        print_debug = False
        try:
            print_debug = self.get_config()['debug']
        except:
            pass
        message = 'Failed to cast message to string'
        try:
            message = str(value)
        except:
            pass
        if print_debug or self.is_polling_action:
            self.debug_print(self.__class__.__name__, message)
            self.save_progress(message)
        elif not is_debug:
            self.save_progress(message)

    def _get_rest_data(self, endpoint):
        try:
            url = f'{self._get_base_url()}/{endpoint}'
            self.__print(url, True)
            response = phantom.requests.get(url, verify=False)
            content = json.loads(response.text)
            code = response.status_code
            if 199 < code < 300:
                if 'data' in content and 'container/' not in url:
                    return content['data']
                else:
                    return content
            else:
                return None
        except:
            return None

    def _post_rest_data(self, endpoint, dictionary):
        try:
            url = f'{self._get_base_url()}/{endpoint}'
            self.__print(url, True)
            data = json.dumps(dictionary)
            response = phantom.requests.post(url, data=data, verify=False)
            content = response.text
            code = response.status_code
            if 199 < code < 300:
                if 'data' in content:
                    return content['data']
                else:
                    return content
            else:
                return None
        except:
            return None

    def _get_base_url(self):
        self.__print("_get_base_url()", True)
        port = 443
        try:
            port = self.get_config()['https_port']
        except:
            pass
        return f'https://127.0.0.1:{port}'

    def _get_repository_id(self, scm):
        self.__print(f'Start: _get_repository_id(): {datetime.datetime.now()}', True)
        uri = f'rest/scm?_filter_name="{scm}"'
        response = self._get_rest_data(uri)
        self.__print(f'Repository id for {scm} is {response[0]["id"]}', True)
        self.__print(f'Finish: _get_repository_id(): {datetime.datetime.now()}', True)
        return int(response[0]['id'])

    def _get_cef_keys(self):
        self.__print(f'Start: _get_cef_content(): {datetime.datetime.now()}', True)
        container_id = self.get_container_id()
        uri = f'rest/artifact?_filter_container={container_id}&sort=id&order=asc&page_size=1'
        artifact = self._get_rest_data(uri)
        cef_keys = []
        if artifact:
            for key in artifact[0]['cef'].keys():
                cef_keys.append(key.lower())
        return cef_keys

    def _is_cache_valid(self, timestamp):
        expiration = self.get_config()['cache_expiration']
        now = int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())
        if now - timestamp < expiration:
            return True
        return False

    def _get_cache(self, repo_id, repo_name):
        self.load_state()
        state = self.get_state()
        if self._is_cache_valid(state['timestamp']):
            self.__print('State cache is still valid', False)
            return state['cache'][repo_name]
        else:
            self.__print('State cache is expired, re-caching', False)
            self._cache_playbooks()
            return self._get_playbooks( repo_id, repo_name )

    def _cache_playbooks(self):
        self.__print(f'Start: _cache_playbooks(): {datetime.datetime.now()}', True)
        cache = {}
        try:
            repo_filter = self.get_config()['repository_filter']
            repo_filter = [repo.strip() for repo in repo_filter.split(',')]
            repo_filter = str(repo_filter).replace("'", '"')
            uri = f'rest/scm?_exclude_name__in={repo_filter}'
            self.__print(uri, True)
            repositories = self._get_rest_data(uri)
            for repository in repositories:
                self.__print(json.dumps(repository), True)
                cache[repository['name']] = self._get_playbooks(repository['id'], repository['name'])
            state = {}
            state['cache'] = cache
            state['timestamp'] = int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())
            self.save_state(state)
            self.__print('Finish: _cache_playbooks(): {datetime.datetime.now()}', True)
            return phantom.APP_SUCCESS
        except Exception as e:
            self.__print("Exception thrown", False)
            self.__print(e, False)

    def _get_playbooks(self, repo_id, repo_name):
        self.__print(f'Start: _get_playbooks(): {datetime.datetime.now()}', True)
        playbook_endpoint = f'rest/playbook?_filter_scm={repo_id}&_filter_name__contains=": "&page_size=0'
        playbook_data = self._get_rest_data(playbook_endpoint)
        lookup = {}
        for playbook in playbook_data:
            if ": " in playbook['name']:
                try:
                    cut_index = playbook['name'].index(': ')
                    type_key = playbook['name'][:cut_index]
                    name = playbook['name'][cut_index + 2:]
                    if type_key in lookup:
                        lookup[type_key].append(name)
                    else:
                        lookup[type_key] = []
                        lookup[type_key].append(name)
                except:
                    pass
        self.__print(str(lookup), True)
        self.__print(f'Finish: _get_playbooks(): {datetime.datetime.now()}', True)
        return lookup

    def _run_playbook(self, playbook_string):
        self.__print('_run_playbook()', True)
        success = False
        uri = 'rest/playbook_run'
        data = {"container_id": self.get_container_id(), "playbook_id": playbook_string, "scope": "all", "run": "true"}
        if self._post_rest_data(uri, data) is not None:
            success = True
        return success

    def _handle_run_playbooks(self, param):
        self.__print(f'Start: _execute_playbooks(): {datetime.datetime.now()}', True)
        action_result = self.add_action_result(ActionResult(dict(param)))
        rule = param.get('rule_name')
        product = param.get('product_name')
        scm = param.get('repository_name')
        repo_id = self._get_repository_id(scm)
        executed_playbooks = []
        try:
            playbooks = self._get_cache(repo_id, scm)
            if 'Rule' in playbooks:
                for playbook in playbooks['Rule']:
                    if rule.lower() == playbook.lower():
                        playbook_name = f'{scm}/Rule: {playbook}'
                        if playbook_name not in executed_playbooks:
                            self.__print(playbook_name, True)
                            executed_playbooks.append(playbook_name)
                            self._run_playbook(playbook_name)
            if 'Subject' in playbooks:
                for playbook in playbooks['Subject']:
                    if playbook.lower() in rule.lower():
                        playbook_name = f'{scm}/Subject: {playbook}'
                        if playbook_name not in executed_playbooks:
                            self.__print(playbook_name, True)
                            executed_playbooks.append(playbook_name)
                            self._run_playbook(playbook_name)
            if 'Product' in playbooks and product is not None and product != "":
                products = []
                if ',' in product:
                    for value in product.split(','):
                        products.append(value.strip())
                else:
                    products.append(product)
                for value in products:
                    if value:
                        for playbook in playbooks['Product']:
                            if value.strip().lower() in playbook.lower():
                                playbook_name = f'{scm}/Product: {playbook}'
                                if playbook_name not in executed_playbooks:
                                    self.__print(playbook_name, True)
                                    executed_playbooks.append(playbook_name)
                                    self._run_playbook(playbook_name)
            if 'Field' in playbooks:
                cef_keys = self._get_cef_keys()
                for playbook in playbooks['Field']:
                    if playbook.lower() in cef_keys:
                        playbook_name = f'{scm}/Field: {playbook}'
                        if playbook_name not in executed_playbooks:
                            self.__print(playbook_name, True)
                            executed_playbooks.append(playbook_name)
                            self._run_playbook(playbook_name)
            if executed_playbooks != []:
                action_result.add_data({'match_found': True})
                action_result.add_data({'matches': json.dumps(executed_playbooks)})
            else:
                action_result.add_data({'match_found': False})
                action_result.add_data({'matches': None})
            self.__print(f'{len(executed_playbooks)} playbooks executed', False)
            action_result.set_status(phantom.APP_SUCCESS, f'Successfully executed {len(executed_playbooks)} playbooks')
            self.__print(f'Finish: _execute_playbooks(): {datetime.datetime.now()}', True)
            return phantom.APP_SUCCESS
        except Exception as e:
            self.set_status(phantom.APP_ERROR, 'Exception while running playbooks')
            self.__print(e, False)
            action_result.set_status(phantom.APP_ERROR, 'Error processing playbooks')
            return phantom.APP_ERROR

    def _handle_on_poll(self, param):
        self.__print('start _on_poll()', True)
        action_result = self.add_action_result(ActionResult(dict(param)))
        self.is_polling_action = True
        try:
            self._cache_playbooks()
            self.__print('Poll completed successfully', False)
            action_result.set_status(phantom.APP_SUCCESS, 'Poll completed successfully')
            return phantom.APP_SUCCESS
        except Exception as e:
            self.__print('Poll failed with an exception', False)
            self.__print(e, False)
            action_result.set_status(phantom.APP_ERROR, 'Poll failed with an exception')
            return phantom.APP_ERROR
        
    def _handle_test_connectivity(self, param):
        self.__print("_handle_test_connectivity", True)
        action_result = self.add_action_result(ActionResult(dict(param)))
        self.load_state()
        state = self.get_state()
        try:
            self.__print(state['cache'], False)
        except:
            self.__print('State file does not contain a playbook cache yet. Turn on polling to cache playbooks', False)
        test_url = f'{self._get_base_url()}/rest/version'
        self.__print(f'Attempting http get for {test_url}', False)
        response = None
        try:
            response = phantom.requests.get(test_url, verify=False)
            self.__print(response.status_code, True)
        except:
            pass
        if response and 199 < response.status_code < 300:
            version = json.loads(response.text)['version']
            self.__print(f'Successfully retrieved platform version: {version}', False)
            self.__print('Passed connection test', False)
            return action_result.set_status(phantom.APP_SUCCESS)
        else:
            self.__print(f'Failed to reach test url: {test_url}\nCheck your hostname config value', False)
            self.__print('Failed connection test', False)
            return action_result.set_status(phantom.APP_ERROR, f'Failed to reach test url {test_url}')
        
    def handle_action(self, param):
        ret_val = phantom.APP_SUCCESS

        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == 'run_playbooks':
            ret_val = self._handle_run_playbooks(param)

        if action_id == 'on_poll':
            ret_val = self._handle_on_poll(param)

        if action_id == 'test_connectivity':
            ret_val = self._handle_test_connectivity(param)

        return ret_val