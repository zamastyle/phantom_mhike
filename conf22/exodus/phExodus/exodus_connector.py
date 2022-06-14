import phantom.app as phantom
from phantom.action_result import ActionResult
import os
import base64
import json
import requests
import datetime
import encryption_helper


class ExodusConnector(phantom.BaseConnector):

    is_polling_action = False

    def __init__(self):
        super(ExodusConnector, self).__init__()
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

    def _get_headers(self, token_id):
        self.__print('_get_headers()', True)
        HEADERS = {"ph-auth-token": token_id}
        return HEADERS

    def _get_source_headers(self):
        self.__print('_get_source_headers()', True)
        return self._get_headers(self.get_config()['source_api_token'])

    def _get_target_headers(self):
        self.__print('_get_target_headers()', True)
        return self._get_headers(self.get_config()['target_api_token'])

    def _get_rest_data(self, base_url, endpoint, headers):
        self.__print(f'Start: _get_rest_data(): {datetime.datetime.now()}', True)
        try:
            if not base_url.endswith('/'):
                base_url = f'{base_url}/'
            url = f'{base_url}{endpoint}'
            self.__print(url, True)
            response = requests.get(url, headers=headers, verify=False)
            content = json.loads(response.text)
            code = response.status_code
            if code == 200:
                if 'data' in content and 'container/' not in url:
                    self.__print(f'Finish: _get_rest_data(): {datetime.datetime.now()}', True)
                    return content['data']
                else:
                    self.__print(f'Finish: _get_rest_data(): {datetime.datetime.now()}', True)
                    return content
            else:
                return None
        except:
            return None

    def _get_source_rest_data(self, endpoint):
        self.__print(f'Start: _get_source_rest_data(): {datetime.datetime.now()}', True)
        headers = self._get_source_headers()
        base_url = self.get_config()['source_base_url']
        return self._get_rest_data(base_url, endpoint, headers)

    def _get_target_rest_data(self, endpoint):
        self.__print(f'Start: _get_target_rest_data(): {datetime.datetime.now()}', True)
        headers = self._get_target_headers()
        base_url = self.get_config()['target_base_url']
        return self._get_rest_data(base_url, endpoint, headers)

    def _post_rest_data(self, base_url, endpoint, headers, dictionary):
        self.__print(f'Start: _post_rest_data(): {datetime.datetime.now()}', True)
        try:
            if not base_url.endswith('/'):
                base_url = f'{base_url}/'
            url = f'{base_url}{endpoint}'
            self.__print(url, True)
            data = json.dumps(dictionary)
            response = requests.post(url, headers=headers, data=data, verify=False)
            content = response.text
            code = response.status_code
            if code == 200:
                if 'data' in content:
                    self.__print(f'Finish: _post_rest_data(): {datetime.datetime.now()}', True)
                    return content['data']
                else:
                    self.__print(f'Finish: _post_rest_data(): {datetime.datetime.now()}', True)
                    return content
            else:
                return None
        except:
            return None

    def _post_source_rest_data(self, endpoint, dictionary):
        self.__print(f'Start: _post_source_rest_data(): {datetime.datetime.now()}', True)
        headers = self._get_source_headers()
        base_url = self.get_config()['source_base_url']
        return self._post_rest_data(base_url, endpoint, headers, dictionary)

    def _post_target_rest_data(self, endpoint, dictionary):
        self.__print(f'Start: _post_target_rest_data(): {datetime.datetime.now()}', True)
        headers = self._get_target_headers()
        base_url = self.get_config()['target_base_url']
        return self._post_rest_data(base_url, endpoint, headers, dictionary)

    def _post_asset(self, asset):
        mysession = requests.Session()
        mysession.verify = False
        mysession.headers = self._get_target_headers()
        url = f'{self.get_config()["target_base_url"]}rest/asset'
        mysession.post(url, json=asset)

    def _get_custom_functions(self, repo_id, min_id):
        self.__print(f'Start: _get_custom_functions(): {datetime.datetime.now()}', True)
        function_endpoint = ('rest/custom_function'
                            f'?_filter_scm={repo_id}'
                            f'&_filter_id__gt={min_id}'
                             '&_filter_disabled=False'
                             '&_filter_passed_validation=True'
                             '&_filter_draft_mode=False')
        function_data = self._get_source_rest_data(function_endpoint)
        self.__print(f'Finish: _get_custom_functions(): {datetime.datetime.now()}', True)
        return function_data

    def _build_playbook_id_cache(self, playbook_data):
        self.__print(f'Start: _build_playbook_id_cache(): {datetime.datetime.now()}', True)
        cache = []
        for playbook in playbook_data:
          cache.append(playbook['id'])
        return cache

    def _swap_function_cache(self, repo_id):
        self.__print(f'Start: _swap_function_cache(): {datetime.datetime.now()}', True)
        self.load_state()
        current_state = self.get_state()
        watermark = None
        try:
            watermark = str(current_state['function_watermark'])
        except:
            self.__print('Exception thrown while reading in function cache. Resetting cf states', True)
        function_endpoint = ('rest/custom_function'
                            f'?_filter_scm={repo_id}'
                             '&page_size=1'
                             '&sort=id'
                             '&order=desc'
                             '&_filter_disabled=False'
                             '&_filter_passed_validation=True'
                             '&_filter_draft_mode=False')
        function_data = self._get_source_rest_data(function_endpoint)
        if function_data:
            try:
                for function in function_data:
                    current_state['function_watermark'] = function['id']
            except:
                current_state['function_watermark'] = 0
            if watermark is None or watermark == '':
                watermark = 0
            if current_state['function_watermark'] is None or current_state['function_watermark'] == '':
                current_state['function_watermark'] = 0
        else:
            current_state['function_watermark'] = 0
        self.save_state(current_state)
        return watermark

    def _swap_playbook_cache(self, repo_id):
        self.__print(f'Start: _swap_playbook_cache(): {datetime.datetime.now()}', True)
        self.load_state()
        current_state = self.get_state()
        old_cache = None
        try:
            old_cache = current_state['playbook_cache']
        except:
            self.__print('Exception thrown while reading in cache. Resetting app states', True)
        playbook_url = ('rest/playbook'
                       f'?_filter_scm={repo_id}'
                        '&_filter_tags__contains="prod"'
                        '&page_size=0')
        playbook_data = self._get_source_rest_data(playbook_url)
        new_cache = self._build_playbook_id_cache(playbook_data)
        current_state['playbook_cache'] = new_cache
        if old_cache is None or old_cache == []:
            old_cache = new_cache
        self.save_state(current_state)
        return old_cache

    def _get_functions(self, repo_id, min_function_id):
        self.__print(f'Start: _get_functions(): {datetime.datetime.now()}', True)
        playbook_endpoint = ('rest/custom_function'
                            f'?_filter_scm={repo_id}'
                             '&page_size=0'
                            f'&_filter_id__gt={min_function_id}'
                             '&sort=id'
                             '&order=desc'
                             '&_filter_disabled=False'
                             '&_filter_passed_validation=True'
                             '&_filter_draft_mode=False')
        function_data = self._get_source_rest_data(playbook_endpoint)
        self.__print(f'Finish: _get_functions(): {datetime.datetime.now()}', True)
        return function_data

    def _get_playbooks(self, repo_id, ignore_playbooks):
        self.__print(f'Start: _get_playbooks(): {datetime.datetime.now()}', True)
        playbook_endpoint = ('rest/playbook'
                            f'?_filter_scm={repo_id}'
                             '&_filter_tags__contains="prod"'
                            f'&_exclude_id__in={ignore_playbooks}'
                             '&page_size=0')
        playbook_data = self._get_source_rest_data(playbook_endpoint)
        self.__print(f'Finish: _get_playbooks(): {datetime.datetime.now()}', True)
        return playbook_data

    def _create_playbook_artifact(self, playbook_json):
        self.__print(f'_create_playbook_artifact(): {datetime.datetime.now()}', True)
        artifact = {
            "cef": {
                "playbook_name": playbook_json['name'],
                "playbook_id": playbook_json['id']
            },
            "label": "playbook",
            "name": playbook_json['name'],
            "source_data_identifier": f'Exodus-{datetime.datetime.now()}-{playbook_json["id"]}',
            "severity": "low"
        }
        return artifact

    def _create_function_artifact(self, function_json):
        self.__print(f'_create_function_artifact(): {datetime.datetime.now()}', True)
        artifact = {
            "cef": {
                "custom_function_name": function_json['name'],
                "custom_function_id": function_json['id']
            },
            "label": "custom_function",
            "name": function_json['name'],
            "source_data_identifier": f'Exodus-{datetime.datetime.now()}-{function_json["id"]}',
            "severity": "low"
        }
        return artifact

    def _add_comment(self, container_id, comment_string):
        endpoint = 'rest/container_comment'
        comment = {
            "container_id": container_id,
            "comment": comment_string
        }
        self._post_source_rest_data(endpoint, comment)

    def _get_asset_details(self, asset_name):
        uri = f'rest/asset?_filter_name="{asset_name}"'
        asset_json = self._get_source_rest_data(uri)[0]
        return asset_json

    def _does_app_exist(self, app_name):
        uri = f'rest/app?_filter_name="{app_name}"'
        app_data = self._get_target_rest_data(uri)
        if app_data == []:
            return False
        else:
            return True

    def _create_app_artifact(self, app_name):
        self.__print(f'_create_app_artifact(): {datetime.datetime.now()}', True)
        artifact = {
            "cef": {
                "app_name": app_name
            },
            "label": "app",
            "name": app_name,
            "source_data_identifier": f'Exodus-{datetime.datetime.now()}-{app_name}',
            "severity": "low"
        }
        return artifact

    def _does_asset_exist(self, asset_name):
        uri = f'rest/asset?_filter_name="{asset_name}"'
        asset_data = self._get_target_rest_data(uri)
        if asset_data == []:
            return False
        else:
            return True

    def _create_asset_artifact(self, asset_name):
        asset_json = self._get_asset_details(asset_name)
        self.__print(f'_create_asset_artifact(): {datetime.datetime.now()}', True)
        artifact = {
            "cef": {
                "asset_name": asset_json['name'],
                "asset_id": asset_json['id']
            },
            "label": "asset",
            "name": asset_json['name'],
            "source_data_identifier": f'Exodus-{datetime.datetime.now()}-{asset_json["id"]}',
            "severity": "low"
        }
        return artifact

    def _create_approval_container(self, artifacts):
        self.__print(f'_create_approval_container(): {datetime.datetime.now()}', True)
        endpoint = 'rest/container'
        container = {
            "artifacts": artifacts,
            "data": {},
            "label": "exodus",
            "name": "Prod Request",
            "container_type": "default"
        }
        try:
            tenant = self.get_config()['source_tenant_id']
            if self.get_config()['source_tenant_id'] is not None:
                container["tenant_id"] = str(tenant)
        except:
            pass
        self._post_source_rest_data(endpoint, container)
        return True

    def _get_unresolved_containers(self):
        self.__print(f'_get_unresolved_containers: {datetime.datetime.now()}', True)
        tenant = None
        try: 
            tenant = self.get_config()['source_tenant_id']
        except:
            pass
        if tenant is not None:
            endpoint = ('rest/container'
                        '?_exclude_status=3'
                        '&_filter_label="exodus"'
                       f'&_filter_tenant={self.get_config()["source_tenant_id"]}'
                        '&page_size=0')
        else:
            endpoint = ('rest/container'
                        '?_exclude_status=3'
                        '&_filter_label="exodus"')
        containers = self._get_source_rest_data(endpoint)
        return containers

    def _is_container_approved(self, container_id):
        self.__print(f'_is_container_approved: {datetime.datetime.now()}', True)
        endpoint = (f'rest/container/{container_id}/artifacts'
                     '?_filter_cef__status="accepted"'
                     '&_filter_label="approval"'
                     '&_filter_name="confirmation"'
                     '&_filter_source_data_identifier__endswith="validated"')
        approvals = self._get_source_rest_data(endpoint)
        if approvals['count'] != 0:
            return True
        else:
            return False

    def _get_asset_artifacts(self, container_id):
        self.__print(f'_get_asset_artifacts: {datetime.datetime.now()}', True)
        endpoint = f'rest/container/{container_id}/artifacts?_filter_label="asset"'
        app_data = self._get_source_rest_data(endpoint)['data']
        return app_data

    def _get_playbook_artifacts(self, container_id):
        self.__print(f'_get_playbooks_artifacts: {datetime.datetime.now()}', True)
        endpoint = f'rest/container/{container_id}/artifacts?_filter_label="playbook"'
        playbook_data = self._get_source_rest_data(endpoint)['data']
        return playbook_data

    def _get_function_artifacts(self, container_id):
        self.__print(f'_get_function_artifacts: {datetime.datetime.now()}', True)
        endpoint = f'rest/container/{container_id}/artifacts?_filter_label="custom_function"'
        function_data = self._get_source_rest_data(endpoint)['data']
        return function_data

    def _migrate_asset(self, asset_name):
        self.__print(f'_migrate_asset(): {datetime.datetime.now()}', True)
        asset = self._get_asset_details(asset_name)
        rest_params = [
            "action_whitelist",
            "validation",
            "tenants",
            "description",
            "tags",
            "type",
            "primary_voting",
            "product_version",
            "product_name",
            "secondary_voting",
            "configuration",
            "product_vendor",
            "name"
        ]
        new_asset = {}
        endpoint = f'rest/app?_filter_product_name__iexact="{asset["product_name"]}"'
        apps = self._get_source_rest_data(endpoint)
        self.__print(apps, True)
        pws = []
        configs = apps[0]['configuration']
        for config in configs:
            if configs[config]['data_type'] == "password":
                pws.append(config)
        for param in rest_params:
            if 'action_whitelist' not in param:
                if 'tenant' in param:
                    new_asset[param] = []
                    for entry in asset[param]:
                        new_asset[param].append(entry['id'])
                elif 'configuration' in param:
                    configuration = {}
                    for entry in asset[param]:
                        if entry not in pws:
                            configuration[entry] = asset[param][entry]
                        else:
                            value = encryption_helper.decrypt(asset[param][entry], str(asset['id']))
                            configuration[entry] = value
                    new_asset[param] = configuration
                else:
                    new_asset[param] = asset[param]
        uri = 'rest/asset'
        if self._post_target_rest_data(uri, new_asset):
            return True
        else:
            return False

    def _update_source_repository(self):
        try:
            if self.get_config()['source_prod_repo_id']:
                self.__print(f'_update_source_repository(): {datetime.datetime.now()}', True)
                uri = f'rest/scm/{self.get_config()["source_prod_repo_id"]}'
                body = {"pull": True, "force": True}
                self._post_source_rest_data(uri, body)
        except:
            pass

    def _export_tgz(self, type, object_id):
        self.__print(f'_export_tgz(): {datetime.datetime.now()}', True)
        headers = self._get_source_headers()
        base_url = self.get_config()['source_base_url']
        if not base_url.endswith('/'):
            base_url = f'{base_url}/'
        if type == 'playbook':
            file_url = f'{base_url}rest/playbook/{object_id}/export'
            filepath = f'/tmp/exported_playbook_{object_id}.tgz'
        else:
            file_url = f'{base_url}rest/custom_function/{object_id}/export'
            filepath = f'/tmp/exported_function_{object_id}.tgz'
        response = None
        try:
            response = requests.get(file_url, headers=headers, verify=False)
        except Exception as e:
            self.__print(e, False)
        try:
            self.__print(f'HTTP Response code: {response.status_code}', True)
            if 199 < response.status_code < 300:
                if response.content:
                    with open(filepath, 'wb') as output:
                       output.write(response.content)
                    self.__print(f'Successfully exported to {filepath}', True)
                    return True
                else:
                    self.__print('No content identified. Cannot export playbook', True)
                    return False
            else:
                self.__print(f'Status {response.status_code}: Cannot export playbook', True)
                return False
        except Exception as e:
            self.__print(e, False)
            return False

    def _import_tgz(self, type, object_id):
        self.__print(f'_import_tgz(): {datetime.datetime.now()}', True)
        headers = self._get_target_headers()
        base_url = self.get_config()['target_base_url']
        if not base_url.endswith('/'):
            base_url = f'{base_url}/'
        repo = self.get_config()['target_repo_id']
        if type == 'playbook':
            filepath = f'/tmp/exported_playbook_{object_id}.tgz'
            post_url = f'{base_url}rest/import_playbook'
        else:
            filepath = f'/tmp/exported_function_{object_id}.tgz'
            post_url = f'{base_url}rest/import_custom_function'
        body = {"scm": repo, "force": True}
        f = open(filepath, 'rb')
        try:
            encoded = base64.encodebytes(f.read())
            if type == 'playbook':
                body['playbook'] = str(encoded, 'utf-8')
            else:
                body['custom_function'] = str(encoded, 'utf-8')
            resp = requests.post(post_url, json=body, headers=headers, verify=False)
            if 199 < resp.status_code < 300:
                self.__print(f'SUCCESS: {json.loads(resp.text)["message"]}', True)
                f.close()
                os.remove(filepath)
                self._update_source_repository()
                return True
            else:
                self.__print(f'FAILED: {json.loads(resp.text)["message"]}', True)
                f.close()
                os.remove(filepath)
                return False
        except Exception as e:
            self.__print(e, False)
            f.close()
            os.remove(filepath)
            return False

    def _migrate_playbook(self, playbook_id):
        self.__print(f'_migrate_playbook(): {datetime.datetime.now()}', True)
        export_status = self._export_tgz('playbook', playbook_id)
        if export_status:
            import_status = self._import_tgz('playbook', playbook_id)
            if import_status:
                return True
            else:
                self.__print(f'Failed to import playbook {playbook_id}', True)
                return False
        else:
            self.__print(f'Failed to export playbook {playbook_id}', True)
            return False

    def _migrate_function(self, function_id):
        self.__print(f'_migrate_fuction(): {datetime.datetime.now()}', True)
        export_status = self._export_tgz('function', function_id)
        if export_status:
            import_status = self._import_tgz('function', function_id)
            if import_status:
                return True
            else:
                self.__print(f'Failed to import function {function_id}', True)
                return False
        else:
            self.__print(f'Failed to export function {function_id}', True)
            return False

    def _resolve_container(self, container):
        self.__print(f'_resolve_container(): {datetime.datetime.now()}', True)
        uri = f'rest/container/{container["id"]}'
        response = self._get_source_rest_data(uri)
        self.__print(response, True)
        status = response['status']
        status = 'closed'
        update_data = {}
        update_data['status'] = status
        response = self._post_source_rest_data(uri, update_data)
        return False
    
    def _handle_test_connectivity(self, param):
        self.__print('Testing automation user API tokens', False)
        uri = 'rest/scm'
        self.__print('Testing source token', False)
        response = self._get_source_rest_data(uri)
        self.__print(response, True)
        if not response:
            self.set_status(phantom.APP_ERROR)
            self.__print('Failed to connect. Make sure source token is correct.', False)
            return phantom.APP_ERROR
        self.__print('Testing target token', False)
        response = self._get_target_rest_data(uri)
        self.__print(response, True)
        if not response:
            self.set_status(phantom.APP_ERROR)
            self.__print('Failed to connect. Make sure target token is correct.', False)
            return phantom.APP_ERROR
        self.set_status(phantom.APP_SUCCESS)
        self.__print('All tokens authenticated properly', False)
        return phantom.APP_SUCCESS
    
    def _handle_add_approval(self, param):
        self.__print('_add_approval_artifact()', True)
        action_result = self.add_action_result(ActionResult(dict(param)))
        artifact = {
            "cef": {
                "status": "accepted"
            },
            "container_id": self.get_container_id(),
            "label": "approval",
            "name": "confirmation",
            "source_data_identifier": f'Exodus-{datetime.datetime.now()}-validated',
            "severity": "low"
        }
        self.save_artifact(artifact)
        action_result.set_status(phantom.APP_SUCCESS)
        self.__print('Successfully saved artifact', True)
        return phantom.APP_SUCCESS

    def _handle_on_poll(self):
        self.__print("polling", True)
        ignore_playbooks = self._swap_playbook_cache(self.get_config()['source_dev_repo_id'])
        min_function_id = self._swap_function_cache(self.get_config()['source_dev_repo_id'])
        candidate_playbooks = self._get_playbooks(self.get_config()['source_dev_repo_id'], ignore_playbooks)
        for candidate in candidate_playbooks:
            artifacts = []
            artifacts.append(self._create_playbook_artifact(candidate))
            for app in candidate['metadata']['apps']:
                if not self._does_app_exist(app):
                    artifacts.append(self._create_app_artifact(app))
            for asset in candidate['metadata']['assets']:
                if not self._does_asset_exist(asset):
                    artifacts.append(self._create_asset_artifact(asset))
            container = self._create_approval_container(artifacts)

        candidate_functions = self._get_functions(self.get_config()['source_dev_repo_id'], min_function_id)
        if candidate_functions:
            for candidate in candidate_functions:
                artifacts = []
                artifacts.append(self._create_function_artifact(candidate))
                container = self._create_approval_container(artifacts)

        for container in self._get_unresolved_containers():
            if self._is_container_approved(container['id']):
                for asset in self._get_asset_artifacts(container['id']):
                    if not self._migrate_asset(asset['cef']['asset_name']):
                        self._add_comment(container['id'], 'Failed to migrate asset. Does it still exist?')
                for playbook in self._get_playbook_artifacts(container['id']):
                    if not self._migrate_playbook(playbook['cef']['playbook_id']):
                        self._add_comment(container['id'], 'Failed to export playbook. Has it been updated since this request was put in?')
                for function in self._get_function_artifacts(container['id']):
                    if not self._migrate_function(function['cef']['custom_function_id']):
                        self._add_comment(container['id'], 'Failed to export custom function. Has it been updated since this request was put in?')
                self._resolve_container(container)

        self.set_status(phantom.APP_SUCCESS)
        return phantom.APP_SUCCESS

    def handle_action(self, param):
        self.__print(f'Start: _handle_action(): {datetime.datetime.now()}', True)
        action = self.get_action_identifier()
        ret_val = phantom.APP_SUCCESS
        if action == 'test_connectivity':
            ret_val = self._handle_test_connectivity(param)
        if action == 'add_approval':
            ret_val = self._handle_add_approval(param)
        elif action == 'on_poll':
            self.is_polling_action = True
            ret_val = self._handle_on_poll()

        self.__print(f'Finish: _handle_action(): {datetime.datetime.now()}', True)
        return ret_val
