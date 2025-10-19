import copy
import json
import uuid
from typing import Dict

import xmltodict
from lxml import etree

from utils_mobile.specialCheck import *


def get_words_in_certain_length(text, length=10):
    words = text.split()
    if len(words) > length:
        return ' '.join(words[:length])
    else:
        return ' '.join(words)


class UIXMLTree:
    def __init__(self):
        self.root = None
        self.cnt = None
        self.node_to_xpath: Dict[str, list[str]] = {}
        self.node_to_name = None
        self.remove_system_bar = None
        self.processors = None
        self.app_name = None
        self.myTree = None
        self.xml_dict = None  # dictionary: processed xml
        self.processors = [self.xml_sparse, self.merge_none_act]
        self.lastTree = None
        self.mapCount = {}
        self.use_bounds = False
        self.merge_switch = False
        self.all_bounds = {}

    def process(self, xml_string, app_info=None, level=1, str_type="json", remove_system_bar=True, use_bounds=False,
                merge_switch=False):
        self.xml_string = xml_string
        self.root = etree.fromstring(xml_string.encode('utf-8'))
        self.cnt = 0
        self.node_to_xpath: Dict[str, list[str]] = {}
        self.node_to_name = {}
        self.remove_system_bar = remove_system_bar

        self.app_name = None
        self.lastTree = self.myTree
        self.myTree = None
        self.use_bounds = use_bounds
        self.merge_switch = merge_switch

        # for gaode
        self.gd_recommend_node = None
        self.gd_recycler_node = None

        # from fine-grained to coarse-grained observation
        for processor in self.processors[:level]:
            processor()
        self.reindex()

        self.xml_dict = xmltodict.parse(etree.tostring(self.root, encoding='utf-8'), attr_prefix="")
        self.traverse_dict(self.xml_dict)
        if "json" == str_type:
            return json.dumps(self.xml_dict, indent=4, ensure_ascii=False).replace(": {},", "").replace(": {}", "")
        elif "plain_text" == str_type:
            return self.dict_to_plain_text(self.xml_dict)
        else:
            raise NotImplementedError

    def insert_node(self, parent, index, attrib_dict):
        new_node = etree.Element('Node')

        for k, v in attrib_dict.items():
            new_node.set(k, v)

        parent.insert(index, new_node)

    def append_node(self, parent, attrib_dict):
        new_node = etree.Element('Node')

        for k, v in attrib_dict.items():
            new_node.set(k, v)

        parent.append(new_node)

    def find_smallest_enclosing_node(self, root, bounds):
        smallest_node = None
        if 'bounds' in root.attrib and check_bounds_containing(bounds, root.attrib['bounds']):
            smallest_node = root
            for child in root:
                candidate = self.find_smallest_enclosing_node(child, bounds)
                if candidate is not None:
                    smallest_node = candidate
        return smallest_node

    def find_nodes_for_bounds(self, root, bounds_list):
        result = []
        for label, bounds in bounds_list:
            node = self.find_smallest_enclosing_node(root, bounds)
            result.append([label, bounds, node])

        # add new nodes
        for label, bounds, parent in result:
            attrib_dict = {
                "index": "0",
                "text": label,
                "resource-id": "",
                "class": "android.widget.TextView",
                "package": parent.attrib['package'],
                "content-desc": "",
                "checkable": "false",
                "checked": "false",
                "clickable": "false",
                "enabled": "false",
                "focusable": "false",
                "focused": "false",
                "scrollable": "false",
                "long-clickable": "false",
                "password": "false",
                "selected": "false",
                "bounds": coords_to_bounds(bounds)
            }
            self.append_node(
                parent=parent,
                index='0',
                attrib_dict=attrib_dict,
            )
        return result

    def dict_to_plain_text(self, xml_dict, indent=0):
        result = ""
        for key, value in xml_dict.items():
            result += " " * indent + str(key) + ": "
            if isinstance(value, dict):
                result += "\n" + self.dict_to_plain_text(value, indent + 4)
            else:
                result += str(value) + "\n"
        return result

    def should_remove_node(self, node):
        # remove system ui elements, e.g, battery, wifi and notifications
        # if self.remove_system_bar and node.attrib['package'] == "com.android.systemui":
        #     return True

        #  remove invalid element
        if not check_valid_bounds(node.attrib["bounds"]):
            return True

        # remove non-visible element
        parent = node.getparent()
        if parent is not None and 'bounds' in parent.attrib:
            if not check_bounds_containing(node.attrib['bounds'], parent.attrib['bounds']):
                return True

        # don't remove functional element
        for p in ["checkable", "checked", "clickable", "focusable", "scrollable", "long-clickable", "password",
                  "selected"]:
            if node.attrib[p] == "true":
                return False

        # don't remove element with description
        for p in ['text', "content-desc"]:
            if node.attrib[p] != "":
                return False
        return True

    def child_index(self, parent, node):
        # find the index of a given node in its sibling nodes
        for i, v in enumerate(list(parent)):
            if v == node:
                return i
        return -1

    def merge_attribute_in_one_line(self, node):
        node.attrib['description'] = ""
        # text description

        # function description in resource-id and class
        if node.attrib['class'] != "":
            node.attrib['description'] += node.attrib['class'] + " "
        # if node.attrib['resource-id'] != "":
        #     node.attrib['description'] += node.attrib['resource-id'] + " "
        # action
        node.attrib['description'] += ';' + node.attrib['action'] + '; '

        # status
        for attrib in ['checked', 'password', 'selected']:
            if node.attrib[attrib] == "true":
                node.attrib['description'] += attrib + ' '
        if node.attrib['checkable'] == "true" and node.attrib['checked'] == "false":
            node.attrib['description'] += 'unchecked '

        # extend status
        extend_status = ";"

        if node.attrib['password'] == "true":
            extend_status += ' you can input password, '
        if node.attrib['selected'] == "true":
            extend_status += ' selected, '
        node.attrib['description'] += extend_status

        # func-desc
        node.attrib['description'] += ";" + node.attrib['func-desc']
        node.attrib['description'] = node.attrib['description'].replace("\n", "")
        # map functional attributes to support actions

        # clean attribute
        # for attrib in ['index', 'text', 'resource-id', 'package', 'content-desc', 'enabled', 'focused',
        #                'visible-to-user', 'bounds', 'class', 'checkable', 'checked', 'clickable', 'focusable',
        #                'scrollable', 'long-clickable', 'password',
        #                'selected', 'func-desc', 'action']:
        for attrib in ['index', 'text', 'resource-id', 'package', 'content-desc', 'enabled', 'focused',
                       'class', 'checkable', 'checked', 'clickable', 'focusable',
                       'scrollable', 'long-clickable', 'password',
                       'selected', 'func-desc', 'action']:
            del node.attrib[attrib]
        if 'NAF' in node.attrib:
            del node.attrib['NAF']

    def get_xpath(self, node):
        if node.tag == 'hierarchy':
            return '/'
        else:
            if node.attrib['resource-id'] != "":
                transfer_resource_id = node.attrib['resource-id']
                my_path = f'//*[@resource-id=\'{transfer_resource_id}\']'
                candi_nodes = self.root.xpath(my_path)
                if len(candi_nodes) == 1:
                    return my_path

            parent = node.getparent()
            children = parent.xpath(f'./*[@class="{node.attrib["class"]}"]')
            index = children.index(node) + 1
            return parent.attrib['xpath2'] + '/' + node.attrib['class'] + f'[{index}]'

    def get_attr_count(self, collection_key, key):
        if collection_key not in self.mapCount:
            return 0
        if key not in self.mapCount[collection_key]:
            return 0
        return self.mapCount[collection_key][key]

    def inc_attr_count(self, collection_key, key):

        if collection_key not in self.mapCount:
            self.mapCount[collection_key] = {key: 1}
        elif key not in self.mapCount[collection_key]:
            self.mapCount[collection_key][key] = 1
        else:
            self.mapCount[collection_key][key] += 1

    def get_xpath_new(self, node):
        array = []
        while node is not None:
            if node.tag != "node":
                break

            parent = node.getparent()
            if self.get_attr_count("tag", node.tag) == 1:
                array.append(f'*[@label="{node.tag}"]')
                break
            elif self.get_attr_count("resource-id", node.attrib["resource-id"]) == 1:
                array.append(f'*[@resource-id="{node.attrib["resource-id"]}"]')
                break
            elif self.get_attr_count("text", node.attrib["text"]) == 1:
                array.append(f'*[@text="{node.attrib["text"]}"]')
                break
            elif self.get_attr_count("content-desc", node.attrib["content-desc"]) == 1:
                array.append(f'*[@content-desc="{node.attrib["content-desc"]}"]')
                break
            elif self.get_attr_count("class", node.attrib["class"]) == 1:
                array.append(f'{node.attrib["class"]}')
                break
            elif parent is None:
                array.append(f'{node.tag}')
            else:
                index = 0
                children = list(parent)
                node_id = children.index(node)
                for _id, child in enumerate(children):
                    if child.attrib["class"] == node.attrib["class"]:
                        index += 1
                    if node_id == _id:
                        break
                array.append(f'{node.attrib["class"]}[{index}]')
            node = parent

        array.reverse()
        xpath = "//" + "/".join(array)
        return xpath

    def get_xpath_all_new(self, node):
        node.attrib['xpath1'] = self.get_xpath_new(node)
        node.attrib['xpath2'] = self.get_xpath(node)
        for child in list(node):
            self.get_xpath_all_new(child)

    def mid_order_remove(self, node):
        children = list(node)
        node.attrib['name'] = ""
        if node.tag == 'node':
            if self.should_remove_node(node):
                # remove node
                parent = node.getparent()
                # insert child nodes into node's parent
                index = self.child_index(parent, node)
                for i, v in enumerate(children):
                    parent.insert(index + i, v)
                parent.remove(node)
            else:
                # pre-process attribute
                # content-desc text
                node.attrib['func-desc'] = ""
                node.attrib['action'] = ""
                # pre desc
                if node.attrib['text'] != "":
                    node.attrib['func-desc'] = node.attrib['text'] + ' '
                if node.attrib['content-desc'] != "":
                    node.attrib['func-desc'] += node.attrib['content-desc'] + ' '

                # pre name
                if node.attrib['class'] != "":
                    if node.attrib['text'] != "":
                        node.attrib['name'] = get_words_in_certain_length(node.attrib['text']) + " " + \
                                              node.attrib['class'].split('.')[-1]
                    elif node.attrib['content-desc'] != "":
                        node.attrib['name'] = get_words_in_certain_length(node.attrib['content-desc']) + " " + \
                                              node.attrib['class'].split('.')[-1]
                    else:
                        node.attrib['name'] = node.attrib['class'].split('.')[-1]

                # pre class
                if node.attrib['class'] != "":
                    if node.attrib['class'].split('.')[-1] in ["View", "FrameLayout", "LinearLayout", "RelativeLayout"]:
                        node.attrib['class'] = ""
                    else:
                        node.attrib['class'] = node.attrib['class'].split('.')[-1]

                # pre resource-id
                if node.attrib['resource-id'] != "":
                    if ":id/" in node.attrib['resource-id']:
                        resrc = node.attrib['resource-id']
                        substring = resrc[resrc.index(":id/") + 4:]
                        node.attrib['resource-id'] = substring
                    else:
                        node.attrib['resource-id'] = ""
                # pre action
                for k, v in {'clickable': 'click', 'scrollable': 'scroll', 'long-clickable': 'long-click',
                             'checkable': 'check'}.items():
                    if node.attrib[k] == "true":
                        node.attrib['action'] += v + ' '
                if node.attrib['action'] == "" and node.attrib['focusable'] == "true":
                    node.attrib['action'] += "focusable "

                # for material_clock_face
                parent = node.getparent()
                if parent.tag == 'node' and "material_clock_face" in parent.attrib['resource-id']:
                    node.attrib['action'] += 'click'

        for child in children:
            self.mid_order_remove(child)

    def get_all_bounds(self, node, parent_keys):
        parent_keys = copy.deepcopy(parent_keys)
        if 'bounds' in node.attrib:
            key = node.attrib['xpath1'] + "_" + node.attrib['xpath2']
            if parent_keys == []:
                self.all_bounds[key] = {'bounds': node.attrib['bounds'], 'children': {}}
            else:
                bounds_dict = self.all_bounds
                for parent_key in parent_keys:
                    bounds_dict = bounds_dict[parent_key]['children']
                bounds_dict[key] = {'bounds': node.attrib['bounds'], 'children': {}}
            parent_keys.append(key)

        for child in list(node):
            self.get_all_bounds(child, parent_keys)

    def remove_children_overlap_with_bounds(self, node, overlap_bounds, current):
        for child in node:
            child_bounds = child.attrib['bounds']
            if check_bounds_intersection(child_bounds, overlap_bounds):
                self.remove_children_overlap_with_bounds(child, overlap_bounds, current)
            else:
                child.getparent().remove(child)
                cur_parent = current.getparent()
                cur_parent.insert(self.child_index(cur_parent, current), child)
                self.queue.append(child)

    def remove_overlap(self):
        self.queue = deque([self.root])

        while self.queue:
            current = self.queue.popleft()
            # for nodes without bounds, just go ahead
            if 'bounds' not in current.attrib:
                self.queue.extend(current.getchildren())
                continue

            current_bounds = current.attrib['bounds']
            # get siblings
            subsequent_siblings = []
            temp = current.getnext()
            while temp is not None:
                subsequent_siblings.append(temp)
                temp = temp.getnext()

            # Check overlaps with each subsequent sibling
            overlap_bounds = None
            for sibling in subsequent_siblings:
                sibling_bounds = sibling.attrib['bounds']
                if check_bounds_intersection(current_bounds, sibling_bounds):
                    overlap_bounds = sibling_bounds
                    break

            if overlap_bounds is not None:
                # Traverse children and handle overlaps
                self.remove_children_overlap_with_bounds(current, overlap_bounds, current)
                current.getparent().remove(current)
            else:
                # No overlap, enqueue all children
                self.queue.extend(current.getchildren())

    def dump_tree(self):
        xml_str = etree.tostring(self.root, encoding='unicode')
        print(xml_str)

    def mid_order_reindex(self, node):
        if node.tag == 'node':
            self.merge_attribute_in_one_line(node)

        node.tag = 'n' + str(uuid.uuid4().hex[:4])

        if node.tag in self.node_to_xpath:
            self.node_to_xpath[node.tag].append(node.attrib['xpath1'])
            self.node_to_xpath[node.tag].append(node.attrib['xpath2'])
        else:
            self.node_to_xpath[node.tag] = [node.attrib['xpath1'], node.attrib['xpath2']]
        self.node_to_xpath[node.tag].append([])
        if node.getparent() is not None:
            parent = node.getparent()
            # check if has xpath
            if parent.tag in self.node_to_xpath:
                self.node_to_xpath[parent.tag][2].append(node.attrib['xpath1'])
                self.node_to_xpath[parent.tag][2].append(node.attrib['xpath2'])
            # add parent xpath to node
            if 'xpath1' in parent.attrib and 'xpath2' in parent.attrib:
                if parent.attrib['xpath1'] != "//" and parent.attrib['xpath2'] != "//":
                    if node.tag in self.node_to_xpath:
                        self.node_to_xpath[node.tag][2].append(parent.attrib['xpath1'])
                        self.node_to_xpath[node.tag][2].append(parent.attrib['xpath2'])
                    else:
                        self.node_to_xpath[node.tag][2] = [parent.attrib['xpath1'], parent.attrib['xpath2']]
            # add sibling node
            children = list(parent)
            for _id, child in enumerate(children):
                if 'xpath1' in child.attrib and 'xpath2' in child.attrib:
                    if node.tag in self.node_to_xpath:
                        self.node_to_xpath[node.tag][2].append(child.attrib['xpath1'])
                        self.node_to_xpath[node.tag][2].append(child.attrib['xpath2'])
                    else:
                        self.node_to_xpath[node.tag][2] = [child.attrib['xpath1'], child.attrib['xpath2']]

        self.node_to_name[node.tag] = node.attrib['name']

        self.cnt = self.cnt + 1

        children = list(node)
        for child in children:
            self.mid_order_reindex(child)
        del node.attrib['xpath1']
        del node.attrib['xpath2']
        del node.attrib['name']

    def merge_description(self, p_desc, c_desc):
        p_list = p_desc.replace(";", " ").replace(",", " ").replace(".", " ").split()
        c_list = c_desc.replace(";", " ").replace(",", " ").replace(".", " ").split(";")
        candi_str = p_desc
        for sub_str in c_list:
            for word in sub_str.split():
                if word not in p_list:
                    candi_str += " " + word

        return candi_str.replace(";", ". ")

    def can_merge_bounds(self, parent_bounds, child_bounds):
        # get bounds
        match_parent = re.findall(r'(\d+)', parent_bounds)
        match_child = re.findall(r'(\d+)', child_bounds)
        x_len_parent = int(match_parent[2]) - int(match_parent[0])
        y_len_parent = int(match_parent[3]) - int(match_parent[1])
        x_len_child = int(match_child[2]) - int(match_child[0])
        y_len_child = int(match_child[3]) - int(match_child[1])

        if y_len_child / y_len_parent > 0.8 and x_len_child / x_len_parent > 0.8:
            return True

        return False

    def mid_order_merge(self, node):
        children = list(node)
        # merge child conditions
        can_merge = False
        if node.tag == 'node' and node.attrib['action'] == "":
            can_merge = True
        if self.use_bounds and node.tag == 'node' and self.can_merge_bounds(node.attrib['bounds'],
                                                                            node.attrib['bounds']):
            can_merge = True
        if self.merge_switch and node.tag == 'node' and node.attrib['checked'] == "true":
            node.attrib['func-desc'] = ', it has a switch and the switch is currently on,'
            can_merge = True
        if self.merge_switch and node.tag == 'node' and node.attrib['checkable'] == "true" and node.attrib[
            'checked'] == "false":
            node.attrib['func-desc'] = ', it has a switch and the switch is currently off,'
            can_merge = True

        if can_merge:
            # add child to parent
            parent = node.getparent()
            if parent.tag == 'node':
                index = self.child_index(parent, node)
                for i, v in enumerate(children):
                    parent.insert(index + i, v)
                # merge desc
                parent.attrib['func-desc'] = self.merge_description(parent.attrib['func-desc'],
                                                                    node.attrib['func-desc'])

                parent.remove(node)
        for child in children:
            self.mid_order_merge(child)

    def traverse_dict(self, _dict):
        key_replace = []

        for key, value in _dict.items():
            # value is also a dict
            if isinstance(value, dict):
                if "rotation" in value:
                    if not self.app_name:
                        app_name = f"The current screenshot's description is shown"
                    elif self.app_name == "home":
                        app_name = f"This is the home screen view."
                    else:
                        app_name = f"The current APP is {self.app_name}."
                    key_replace.append([key, app_name])
                    del value['rotation']
                elif "description" in value:
                    new_key = f"[{key}] {value['description']}"
                    key_replace.append([key, new_key])
                    del value['description']

        for key_pr in key_replace:
            _dict[key_pr[1]] = _dict[key_pr[0]]
            del _dict[key_pr[0]]

        for key, value in _dict.items():
            if isinstance(value, dict):
                self.traverse_dict(value)

    def merge_none_act(self):
        self.mid_order_merge(self.root)

    def reindex(self):
        # self.cnt = 0
        self.mid_order_reindex(self.root)

    def special_check(self):
        current_app = list(self.root)[0].attrib['package']
        try:
            specialcheck = SpecialCheck[current_app](self.xml_string, self.root)
            specialcheck.check()
        except KeyError:
            self.remove_overlap()

    def xml_sparse(self):
        # get all attribute count
        self.mapCount = {}
        for element in self.root.iter():
            self.inc_attr_count("tag", element.tag)
            if element.tag != "node":
                continue
            self.inc_attr_count("resource-id", element.attrib["resource-id"])
            self.inc_attr_count("text", element.attrib["text"])
            self.inc_attr_count("class", element.attrib["class"])
            self.inc_attr_count("content-desc", element.attrib["content-desc"])

        # self.get_xpath_all(self.root)
        self.get_xpath_all_new(self.root)
        self.mid_order_remove(self.root)
        self.special_check()
        # save the tree
        self.myTree = copy.copy(self.root)

    def dump_xpath(self):
        json_data = json.dumps(self.node_to_xpath, indent=4, ensure_ascii=False)
        print(json_data)

    def dump_name(self):
        json_data = json.dumps(self.node_to_name, indent=4, ensure_ascii=False)
        print(json_data)

    def get_recycle_nodes(self, root):
        node_list = []
        for element in root.iter():
            if 'scrollable' in element.attrib and element.attrib['scrollable'] == 'true':
                node_list.append(element)
                print(element.attrib['class'], element.attrib['resource-id'], element.attrib['func-desc'])
        return node_list

    def same_subtree(self, tree1, tree2):
        if tree1.attrib['class'] != tree2.attrib['class'] or tree1.attrib['resource-id'] != tree2.attrib[
            'resource-id'] or tree1.attrib['func-desc'] != tree2.attrib['func-desc']:
            return False
        children1 = list(tree1)
        children2 = list(tree2)
        if len(children1) != len(children2):
            return False
        for i in range(len(children1)):
            if not self.same_subtree(children1[i], children2[i]):
                return False
        return True

    def check_unique(self, node, node_list):
        for element in node_list:
            if self.same_subtree(node, element):
                return False
        return True

    def merge_recycle_list(self, recycle_nodes):
        for element in self.root.iter():
            if 'scrollable' in element.attrib and element.attrib['scrollable'] == 'true':
                # find same recycle node
                for node in recycle_nodes:
                    if element.attrib['class'] == node.attrib['class'] and element.attrib['resource-id'] == node.attrib[
                        'resource-id'] and element.attrib['func-desc'] == node.attrib['func-desc']:
                        # merge
                        for child in list(node):
                            if self.check_unique(child, list(element)):
                                element.append(child)

    def check_scroll_bottom(self, tree1, tree2):
        child1 = list(tree1)
        child2 = list(tree2)
        for i in range(len(child1)):
            if not self.same_subtree(child1[i], child2[i]):
                return False
        return True
