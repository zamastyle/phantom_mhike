import phantom.app as phantom
from phantom.action_result import ActionResult
import json


class LinkConnector(phantom.BaseConnector):

    def __init__(self):
        super(LinkConnector, self).__init__()
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
        if print_debug:
            self.debug_print(self.__class__.__name__, message)
            self.save_progress(message)
        elif not is_debug:
            self.save_progress(message)

    def _get_previous_links(self):
        self.__print('_get_previous_links()', True)
        current_links = []
        try:
            query_url = ('{0}/rest/container/{1}/actions'
                         '?_filter_action=%22add%20link%22'
                         '&_filter_status=%22success%22'
                         '&sort=id'
                         '&order=desc'
                         '&page_size=1'
                         '&include_expensive').format(self._get_base_url(), self.get_container_id())
            self.__print(query_url, True)
            response = phantom.requests.get(query_url, verify=False)
            self.__print(response.status_code, True)
            action_id = json.loads(response.text)['data'][0]['id']
            results_url = '{0}/rest/action_run/{1}/app_runs?include_expensive'.format(self._get_base_url(), action_id)
            self.__print(results_url, True)
            response = phantom.requests.get(results_url, verify=False)
            self.__print(response.status_code, True)
            self.__print(json.loads(response.text)['data'][0]['result_data'][0]['data'][0]['linkset'], True)
            links = json.loads(response.text)['data'][0]['result_data'][0]['data'][0]['linkset']
            for link in links:
                current_links.append(link)
                self.__print(link, True)
        except Exception as e:
            self.__print("Exception thrown while gathering previous links", False)
            self.__print(e, False)
        return current_links

    def _sort_links(self, links):
        self.__print('_sort_links()', True)
        descriptors = []
        for link in links:
            if link['descriptor'] not in descriptors:
                descriptors.append(link['descriptor'])
        descriptors.sort()
        sorted_links = []
        for descriptor in descriptors:
            for link in links:
                if link['descriptor'] == descriptor:
                    sorted_links.append(link)
                    break
        return sorted_links

    def _handle_add_link(self, param):
        self.__print('_link()', True)
        self.__print('Single URL: {}'.format(param.get('url')), True)
        self.__print('Single Description: {}'.format(param.get('description')), True)
        self.__print('Link Set: {}'.format(param.get('linkset')), True)
        action_result = self.add_action_result(ActionResult(dict(param)))
        sorting = False
        try:
            sorting = param.get('sort')
        except:
            pass
        processed_links = []
        single_url = param.get('url')
        single_desc = param.get('description')
        all_links = None
        if single_url and single_desc:
            all_links = [{"descriptor": single_desc, "url": single_url}]
            all_links = json.dumps(all_links)
        else:
            all_links = param.get('linkset')
        all_links = all_links.replace('\\', '%5C')
        all_links = json.loads(all_links)
        for link_set in all_links:
            self.__print(link_set, True)
            try:
                if 'descriptor' in link_set and 'url' in link_set and link_set['descriptor'] and link_set['url']:
                    processed_links.append(link_set)
            except:
                self.__print('Missing or null values in link: {}'.format(link_set), False)
        if processed_links:
            if param.get('append'):
                current_links = self._get_previous_links()
                new_descriptors = [link['descriptor'] for link in processed_links]
                for linkset in current_links:
                    if linkset['descriptor'] not in new_descriptors:
                        processed_links.append(linkset)
            if sorting:
                processed_links = self._sort_links(processed_links)
            action_result.add_data({'linkset': processed_links})
            self.__print('Successfully processed links', False)
            action_result.set_status(phantom.APP_SUCCESS, 'Successfully processed links')
            return action_result.get_status()
        else:
            self.__print('Failed to process any links from the input', False)
            action_result.set_status(phantom.APP_ERROR, 'Failed to process any links from the input')
            return action_result.get_status()

    def _get_base_url(self):
        self.__print("_get_base_url()", True)
        port = 443
        try:
            port = self.get_config()['https_port']
        except:
            pass
        return f'https://127.0.0.1:{port}'

    def _handle_test_connectivity(self, param):
        self.__print("_handle_test_connectivity", True)
        action_result = self.add_action_result(ActionResult(dict(param)))
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
        self.__print('handle_action()', True)
        ret_val = phantom.APP_SUCCESS
        if self.get_action_identifier() == 'test_connectivity':
            ret_val = self._handle_test_connectivity(param)
        if self.get_action_identifier() == 'add_link':
            ret_val = self._handle_add_link(param)
        return ret_val


if __name__ == '__main__':
    import sys
    import pudb
    pudb.set_trace()
    if len(sys.argv) < 2:
        print('No test json specified as input')
        exit(0)
    with open(sys.argv[1]) as (f):
        in_json = f.read()
        in_json = json.loads(in_json)
        print( json.dumps(in_json, indent=4) )
        connector = LinkConnector()
        connector.print_progress_message = True
        ret_val = connector._handle_action(json.dumps(in_json), None)
        print( json.dumps(json.loads(ret_val), indent=4) )
    exit(0)
