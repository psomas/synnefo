from util import check_abs_name
from util import check_node_key
from util import is_system_node
from util import check_context
from util import check_string
from util import NameOfSystemNode
from util import NameOfResourcesNode
from util import NameOfGroupsNode
from util import NameOfUsersNode
from util import make_abs_resource_name
from util import make_abs_group_name
from util import make_abs_user_name
from util import reparent_child_name_under
from util import check_abs_resource_name
from util import check_abs_group_name
from util import parent_abs_name_of
from util import relative_child_name_under
from util import make_rel_resource_name
from util import make_rel_group_name
from util import make_rel_user_name
from util import check_name
from util import check_attribute_name
from util import level_of_node
from util import check_abs_name
from util import check_relative_name
from util import is_abs_resource_name
from util import is_abs_group_name
from util import is_abs_user_name

class QuotaDetails(object):
    """
    Quota details, as given by the low-level Quota Holder API
    """
    def __init__(self):
        self.__entity = None
        self.__resource = None
        self.__quantity = None
        self.__capacity = None
        self.__import_limit = None
        self.__export_limit = None
        self.__imported = None
        self.__exported = None
        self.__returned = None
        self.__released = None
        self.__flags = QuotaDetails.default_flags()        
    
    def entity(self):
        return self.__entity
    
    def resource(self):
        return self.__resource
    
    def quantity(self):
        return self.__quantity
    
    def capacity(self):
        return self.__capacity
    
    def import_limit(self):
        return self.__import_limit
    
    def export_limit(self):
        return self.__export_limit
    
    def imported(self):
        return self.__imported
    
    def exported(self):
        return self.__exported
    
    def released(self):
        return self.__released
    
    def flags(self):
        return self.__flags
    
    def current_amount(self):
        def num(x):
            if x is None:
                return 0
            else:
                return x
        
        return  num(self.__quantity) + \
                num(self.__imported) - \
                num(self.__exported) + \
                num(self.__returned) - \
                num(self.__released)

#    def is_unknown(self):
#        return \
#            self.__entity is None and \
#            self.__resource is None and \
#            self.__quantity is None and \
#            self.__capacity is None and \
#            self.__import_limit is None and \
#            self.__export_limit is None and \
#            self.__returned is None and \
#            self.__released is None and \
#            (self.__flags is None or self.__flags == 0)
            
    @classmethod
    def default_flags(cls):
        return 0
    
    @classmethod
    def from_tuple(cls, quota):
        q = QuotaDetails()
        q.__entity = quota[0]
        q.__resource = quota[1]
        q.__quantity = quota[2]
        q.__capacity = quota[3]
        q.__import_limit = quota[4]
        q.__export_limit = quota[5]
        q.__imported = quota[6]
        q.__exported = quota[7]
        q.__returned = quota[8]
        q.__released = quota[9]
        q.__flags = quota[10]
        return q
    
    @classmethod
    def from_dict(cls, d):
        def get(name):
            return d.get(name) or d.get('__' + name) or None
        q = QuotaDetails()
        q.__entity = get('entity')
        q.__resource = get('resource')
        q.__quantity = get('quantity')
        q.__capacity = get('capacity')
        q.__import_limit = get('import_limit')
        q.__export_limit = get('export_limit')
        q.__imported = get('imported')
        q.__exported = get('exported')
        q.__returned = get('returned')
        q.__released = get('released')
        q.__flags = get('flags') or QuotaDetails.default_flags()
        return q
        
    def to_dict(self):
        return {'entity': self.entity(),
                'resource': self.resource(),
                'quantity': self.quantity(),
                'capacity': self.capacity(),
                'import_limit': self.import_limit(),
                'export_limit': self.export_limit(),
                'imported': self.imported(),
                'exported': self.exported(),
                'returned': self.returned(),
                'released': self.released(),
                'flags': self.flags()
                }
        
    def get_attribute_value(self):
        # We always use capacity() as the value of an attribute
        return self.capacity()
    
    def __str__(self):
        return str(self.to_dict())
        
    def __repr__(self):
        return str(self)
    
class NodeAttr(object):
    def __init__(self, name, value,
                 parent_node, for_node,
                 full_name, quota_details):
        check_abs_name(parent_node, 'attribute_parent_node')
        check_abs_name(for_node, 'attribute_for_node')
        check_attribute_name(name, 'attribute_name')
        if not isinstance(value, int):
            raise Exception("Value %s of attribute %s is not an int" % (
                    value, name))
        check_quota_details(quota_details,
                            "quota_details=%s of attribute %s is not a %s" %(
                                quota_details,
                                full_name,
                                QuotaDetails.__name__))
        
        self.__name = name
        self.__value = value
        self.__parent_node = parent_node
        self.__for_node = for_node
        self.__full_name = full_name
        self.__quota_details = quota_details
    
    def name(self):
        return self.__name
    
    def value(self):
        return self.__value
    
    def parent_node(self):
        return self.__parent_node
    
    def for_node(self):
        return self.__for_node
    
    def full_name(self):
        return self.__full_name
    
    def quota_details(self):
        return self.__quota_details
    
    def __str__(self):
        return "%s('%s', %s, %s)" % (self.__class__.__name__,
                                     self.name(),
                                     self.value(),
                                     self.full_name())
        
    def __repr__(self):
        return str(self)
    

class ResourceInfo(object):
    """
    Definition of a global __resource and what it contains.
    """
    def __init__(self, abs_resource_name, resource_quota_details, *attributes):
        check_abs_resource_name(abs_resource_name)
        check_quota_details(resource_quota_details,
                            "resource_quota_details=%s is not a %s" % (
                                resource_quota_details, ResourceInfo.__name__))
        self.__quota_details = resource_quota_details
        self.__abs_name = abs_resource_name
        self.__rel_name = make_rel_resource_name(abs_resource_name)
        for index, attribute in enumerate(attributes):
            check_node_attr(attribute,
                            "Attribute at index %s is not a NodeAttr but %s" % (
                                index, attribute))
        self.__attributes = set(attributes)
    
    def quota_details(self):
        return self.__quota_details
    
    def name(self):
        return self.__abs_name
    
    def rel_name(self):
        return self.__rel_name
    
    def attributes(self):
        return self.__attributes.copy()
    
    def __str__(self):
        return "%s('%s', %s, [%s])" %(self.__class__.__name__,
                                      self.name(),
                                      self.quota_value(),
                                      ', '.join(str(a) for a in self.attributes()))
        
    def __repr__(self):
        return str(self)


class GroupResourceInfo(object):
    """
    Definition of a resource provided by a group
    """
    def __init__(self, abs_group_name, abs_resource_name,
                 resource_quota_details, user_quota_attr):
        check_abs_group_name(abs_group_name)
        check_abs_resource_name(abs_resource_name)
        check_quota_details(resource_quota_details,
                            "quota_details=%s is not a %s" % (
                                resource_quota_details, QuotaDetails.__name__))
        self.__group_name = abs_group_name
        self.__resource_name = abs_resource_name
        
    

class GroupInfo(object):
    """
    Definition of a group, along with the resources it provides.
    """
    def __init__(self, group_node, *group_resources):
        pass

def check_node_attr(node_attr, err_msg):
    if not isinstance(node_attr, NodeAttr):
        raise Exception(err_msg)

def check_quota_details(quota_details, err_msg):
    if not isinstance(quota_details, QuotaDetails):
        raise Exception(err_msg)
    
    
class HighLevelAPI(object):
    """
    High-level QuotaDetails Holder API that supports definitions of resources,
    groups and users and the transfer of __resource quotas from
    respective resources to both groups and users.
    
    Internally it uses the low-level QuotaDetails Holder API, so it maps everything
    into Entities, Resources, Policies and Limits.
    
    High-level API Terminology
    ~~~~~~~~~~~~~~
    
    An absolute name is a name that is either 'system' or contains 'system/' as
    its prefix. It is made of parts separated by slash '/'. It does never
    end in a '/' and it does not contain consecutive '/'s. So, 'system/groups'
    and 'system/resources' are absolute names but 'foo', 'foo/bar',
    'system//groups' and 'system/groups/' are not absolute names.
    
    A node is an __entity whose name is an absolute name, as defined above.
    The root node named 'system' is always present and is enforced by the
    low-level API. This node is called the system node or, symbolically,
    SYSTEM.
    A node is uniquely identified by its absolute name. 
    
    The level of a node is the number of slashes it contains. Equivalently, it
    is the number of its parts minus one. So, SYSTEM has level zero,
    'system/resources' has level one, 'system/resources/pithos+' has level
    two and so on. For a node with a symbolic name A, its level is given
    symbolically as level(A). By definition level(SYSTEM) = 0.
    We subsequently use upper-case letters or words, like SYSTEM, A, B and
    so on, in order to identify nodes.
    
    A node A which is not SYSTEM is the (direct) parent of node B
    if and only if level(A) + 1 = level(B). We denote parenthood symbolically
    by writing parent(B) = A. Also, we say that B is a (direct) child of A.    
    By definition, parent(SYSTEM) = SYSTEM.
        
    A top-level node is a node if level one. There are three top-level nodes,
    namely 'system/resources', 'system/users' and 'system/groups'. The symbolic
    names for these are RESOURCES, USERS and GROUPS respectively.
    RESOURCES is used to model ~okeanos resources, USERS is used to model
    ~okeanos users and GROUPS is used to model ~okeanos groups. By the previous
    definition of parenthood,
    parent(RESOURCES) = parent(USERS) = parent(GROUPS) = SYSTEM.
    
    A (global) __resource R is a node such that parent(R) = RESOURCES.
    A group G is a node such that parent(G) = GROUPS.
    A user U is a node such that parent(U) = USERS.    
    """

    ATTR_NAME_USER='user'
    ATTR_NAME_USER_MAX='user_max'
    ATTR_NAME_GROUP_MAX='group_max'

    def __init__(self, qh = None, **kwd):
        self.__client_key = kwd.get('client_key') or ''
        self.__node_key = kwd.get('node_key') or ''
        
        if qh is None:
            def new_http_qh(url):
                from quotaholder.clients.kamaki import quotaholder_client
                return quotaholder_client(url)
                            
            def check_dict(d):
                if d.has_key('QH_URL'):
                    return kwd['QH_URL']
                elif d.has_key('QH_HOST') and d.has_key('QH_PORT'):
                    return "http://%s:%s/api/quotaholder/v" % (
                        d['QH_HOST'],
                        d['QH_PORT'])
                else:
                    return None
            
            from os import environ
            url = check_dict(kwd) or check_dict(environ)
            if url is None:
                raise Exception("No quota_details holder low-level api specified")
            del environ
            self.__qh = new_http_qh(url)
            
        else:
            self.__qh = qh
            
        self.__context = check_context(kwd.get('context') or {})
        self.__node_keys = {
            NameOfSystemNode: check_string('system_key',
                                           kwd.get('system_key') or ''),
            NameOfResourcesNode: check_string('resources_key',
                                              kwd.get('resources_key') or ''),
            NameOfGroupsNode: check_string('groups_key',
                                           kwd.get('groups_key') or ''),
            NameOfUsersNode: check_string('users_key',
                                           kwd.get('users_key') or '')
        }


    # internal API
    def __create_attribute_of_node_for_resource(self,
                                                node_name,
                                                node_label,
                                                resource_name,
                                                attribute_name,
                                                attribute_value,
                                                quantity,
                                                capacity,
                                                import_limit,
                                                export_limit,
                                                flags):
        #
        check_abs_name(node_name, node_label)
        check_attribute_name(attribute_name)
                
        abs_resource_name = make_abs_resource_name(resource_name)
                
        computed_attribute_name = self.make_full_attribute_name(
            attribute_name,
            node_name,
            abs_resource_name)
        
        quota = self.set_quota(
            entity=node_name,
            resource=computed_attribute_name,
            quantity=quantity,
            capacity=capacity,
            import_limit=import_limit,
            export_limit=export_limit,
            flags=flags)
        
        return NodeAttr(attribute_name, attribute_value, node_name,
                        abs_resource_name, computed_attribute_name, quota)


    #+++##########################################
    # Public, low-level API.
    # We expose some low-level QuotaDetails Holder API
    #+++##########################################

    def qh_list_entities(self, entity, key=''):
        key = key or self.__node_keys.get(entity) or ''
        return self.__qh.list_entities(context=self.__context,
                                       entity=entity,
                                       key=key)
    
    def qh_list_resources(self, entity, key=''):
        key = key or self.__node_keys.get(entity) or ''
        return self.__qh.list_resources(context=self.__context,
                                       entity=entity,
                                       key=key)        
    
    def qh_get_quota(self, entity, resource, key=''):
        key = key or self.__node_keys.get(entity) or ''
        quota_list = self.__qh.get_quota(context=self.__context,
                                   get_quota=[(entity, resource, key)])
        if quota_list:
            quota = quota_list[0]
            return QuotaDetails.from_tuple(quota)
        else:
            return QuotaDetails() # empty
    
    
    def qh_set_quota(self, entity, resource, key,
                     quantity, capacity,
                     import_limit, export_limit, flags):
        key = key or self.__node_keys.get(entity) or ''
        rejected = self.__qh.set_quota(context=self.__context,
                            set_quota=[(entity,
                                        resource,
                                        key,
                                        quantity,
                                        capacity,
                                        import_limit,
                                        export_limit,
                                        flags)])
        if len(rejected) > 0:
            raise Exception("Rejected set_quota for __entity=%s, __resource=%s" % (
                    entity, resource))
        q = QuotaDetails.from_tuple((entity,
                              resource,
                              quantity,
                              capacity,
                              import_limit,
                              export_limit,
                              0, 0, 0, 0,
                              flags))
        return q
        
    
    def qh_create_entity(self,
                         entity,
                         owner,
                         key='',
                         owner_key='',
                         entity_label='__entity'):
        key = self.get_cached_node_key(entity, entity_label)
        owner_key = self.get_cached_node_key(owner)
        
        rejected = self.__qh.create_entity(context=self.__context,
                                    create_entity=[(entity,
                                                    owner,
                                                    key,
                                                    owner_key)])
        if len(rejected) > 0:
            raise Exception("Could not create %s='%s' under '%s'. Probably it already exists?" % (
                    entity_label, entity, owner))
        return entity
        
        
    def qh_get_entity(self, entity, key=''):
        key = key or self.__node_keys.get(entity) or ''
        entity_owners = self.__qh.get_entity(context=self.__context,
                                 get_entity=[(entity, key)])
        if len(entity_owners) == 0:
            return None
        else:
            return entity_owners[0] 
        
    def qh_release_entity(self, entity, key=''):
        key = key or self.__node_keys.get(entity) or ''
        rejected = self.__qh.release_entity(context=self.__context,
                                 release_entity=[(entity, key)])
        if len(rejected) > 0:
            raise Exception("Could not release __entity '%s'" % (entity))
    
    def qh_issue_one_commission(self, target_entity, target_entity_key,
                                owner, owner_key,
                                source_entity, resource, quantity):
        client_key = self.__client_key
        tx_id = self.__qh.issue_commission(
            context=self.__context,
            target=target_entity,
            key=target_entity_key,
            clientkey=client_key,
            owner=owner,
            ownerkey=owner_key,
            provisions=[(source_entity,
            resource,
            quantity)])
        try:
            self.__qh.accept_commission(
                context=self.__context,
                clientkey=client_key,
                serials=[tx_id])
            return tx_id
        except:
            self.__qh.reject_commission(
                context=self.__context,
                clientkey=client_key,
                serials=[tx_id])
        
        
    #---##########################################
    # Public, low-level API.
    # We expose some low-level Quota Holder API
    #---##########################################
    
    
    #+++##########################################
    # Public, high-level API.
    #+++##########################################

    def get_quota(self, entity, resource):
        check_abs_name(entity, '__entity')
        return self.qh_get_quota(entity,
                                 resource,
                                 self.get_cached_node_key(entity))
        
        
    def set_quota(self, entity, resource,
                     quantity, capacity,
                     import_limit, export_limit, flags):
        check_abs_name(entity)
        return self.qh_set_quota(entity=entity,
                                 resource=resource,
                                 key=self.get_cached_node_key(entity),
                                 quantity=quantity,
                                 capacity=capacity,
                                 import_limit=import_limit,
                                 export_limit=export_limit,
                                 flags=flags)
            
    def issue_one_commission(self, target_entity, source_entity,
                                resource, quantity):
        check_abs_name(target_entity, 'target_entity')
        check_abs_name(source_entity, 'source_entity')
        
#        owner=parent_abs_name_of(target_entity, 'parent_target_entity')
#        owner_key = self.get_cached_node_key(owner, 'owner')
        owner = '' # Ignore the owner here. Everything must be set up OK
        owner_key = ''
        try:
            return self.qh_issue_one_commission(
                target_entity=target_entity,
                target_entity_key=self.get_cached_node_key(target_entity),
                owner=owner,
                owner_key=owner_key,
                source_entity=source_entity,
                resource=resource,
                quantity=quantity)
        except Exception, e:
            raise Exception(
                    "Could not transfer %s from '%s' to '%s' for __resource '%s'. Original error is %s: %s" % (
                        quantity, source_entity, target_entity, resource,
                        type(e).__name__, str(e)))


    def get_cached_node_key(self, node_name, node_label='node_name'):
        check_abs_name(node_name, node_label)
        return self.__node_keys.get(node_name) or self.__node_key or ''


    def set_cached_node_key(self, node_name, node_key, node_label='node_name'):
        check_abs_name(node_name, node_label)
        check_node_key(node_key)
        if node_key is None:
            node_key = ''
        self.__node_keys[node_name] = node_key


    def node_keys(self):
        return self.__node_keys.copy() # Client cannot mess with the original
    
    
    def get_node_children(self, node_name):
        check_abs_name(node_name, 'node_name')
        all_entities = self.__qh.list_entities(
            context=self.__context,
            entity=node_name,
            key=self.get_cached_node_key(node_name))
        return [child_node_name for child_node_name in all_entities \
                if child_node_name.startswith(node_name + '/')]
    
    
    def get_toplevel_nodes(self):
        """
        Return all nodes with absolute name starting with 'system/'
        """
        return self.get_node_children(NameOfSystemNode)
    
        
    def get_resources(self):
        self.ensure_resources_node()
        return self.get_node_children(NameOfResourcesNode)
    
    
    def get_groups(self):
        self.ensure_groups_node()
        return self.get_node_children(NameOfGroupsNode)
    
    
    def get_users(self):
        self.ensure_users_node()
        return self.get_node_children(NameOfUsersNode)
    

    def ensure_node(self, abs_node_name, label='abs_node_name'):
        if not self.node_exists(abs_node_name, label):
            return self.create_node(abs_node_name, label)
        else:
            return abs_node_name


    def ensure_top_level_nodes(self):
        return  [self.ensure_resources_node(),
                 self.ensure_users_node(), 
                 self.ensure_groups_node()]
    
    
    def ensure_resources_node(self):
        """
        Ensure that the node 'system/resources' exists.
        """
        return self.ensure_node(NameOfResourcesNode, 'NameOfResourcesNode')


    def ensure_groups_node(self):
        """
        Ensure that the node 'system/groups' exists.
        """
        return self.ensure_node(NameOfGroupsNode, 'NameOfGroupsNode')


    def ensure_users_node(self):
        """
        Ensure that the node 'system/users' exists.
        """
        return self.ensure_node(NameOfUsersNode, 'NameOfGroupsNode')


    def node_exists(self, abs_node_name, label='abs_node_name'):
        """
        Checks if a node with the absolute name ``abs_node_name`` exists.
        
        Returns ``True``/``False`` accordingly.
        """
        check_abs_name(abs_node_name, label)
        node_key = self.get_cached_node_key(abs_node_name)
        entity_owner_list = self.__qh.get_entity(
            context=self.__context,
            get_entity=[(abs_node_name, node_key)]
        )
        return len(entity_owner_list) == 1 # TODO: any other check here?


    def group_exists(self, group_name):
        abs_group_name = make_abs_group_name(group_name)
        return self.node_exists(abs_group_name, 'abs_group_name')


    def resource_exists(self, resource_name):
        abs_resource_name = make_abs_resource_name(resource_name)
        return self.node_exists(abs_resource_name, 'abs_resource_name')


    def user_exists(self, user_name):
        abs_user_name = make_abs_user_name(user_name)
        return self.node_exists(abs_user_name, 'abs_user_name')
    
    
    def create_node(self, node_name, node_label):
        """
        Creates a node with an absolute name ``node_name``.
        
        If the hierarchy up to ``node_name`` does not exist, then it is
        created on demand.
        
        Returns the absolute ``node_name``.
        
        The implementation maps a node to a QuotaDetails Holder __entity.
        """
#        print "Creating %s=%s" % (node_label, node_name)
        check_abs_name(node_name, node_label)
        
        if is_system_node(node_name):
            # SYSTEM always exists
            return node_name

        parent_node_name = parent_abs_name_of(node_name, node_label)
        # Recursively create hierarchy. Beware the keys must be known.
        self.ensure_node(parent_node_name, node_label)

        node_key = self.get_cached_node_key(node_name)
        parent_node_key = self.get_cached_node_key(parent_node_name)
        
        return self.qh_create_entity(entity=node_name,
                                     owner=parent_node_name,
                                     key=node_key,
                                     owner_key=parent_node_key,
                                     entity_label=node_label)


    def make_full_attribute_name(self, attribute_name, parent_node, for_node=''):
        if (for_node == '') or (for_node is None):
            for_node = parent_node
        check_attribute_name(attribute_name)
        check_abs_name(parent_node, 'parent_node')        
        check_abs_name(for_node, 'attribute_for_node')
        
        if parent_node == for_node:
            return "%s::%s" % (attribute_name, parent_node)
        else:
            return "%s::%s::%s" % (attribute_name, parent_node, for_node)


    def split_full_attribute_name(self, name):
        data = name.split("::")
        if len(data) == 2:
            return (data[0], data[1], data[1])
        elif len(data) == 3:
            return (data[0], data[1], data[2])
        else:
            raise Exception("Bad form of attribute name: '%s'" % (name))


    def get_resource_info(self, name):
        if not self.resource_exists(name):
            raise Exception("Unknown __resource '%s'" % (name))
        
        abs_resource_name = make_abs_resource_name(name)
        
        
        resource_quota = self.get_quota(entity=abs_resource_name,
                                        resource=abs_resource_name)
        
        user_attr_full_name = self.make_full_attribute_name(
            HighLevelAPI.ATTR_NAME_USER, abs_resource_name)
        user_quota_details = self.get_quota(
            entity=abs_resource_name, resource=user_attr_full_name)
        user_attr = NodeAttr(HighLevelAPI.ATTR_NAME_USER,
                             user_quota_details.get_attribute_value(),
                             abs_resource_name,
                             abs_resource_name,
                             user_attr_full_name,
                             user_quota_details)

        user_max_attr_full_name = self.make_full_attribute_name(
                                        HighLevelAPI.ATTR_NAME_USER_MAX,
                                        abs_resource_name)
        user_max_quota_details = self.get_quota(
                                        entity=abs_resource_name,
                                        resource=user_max_attr_full_name)
        user_max_attr = NodeAttr(HighLevelAPI.ATTR_NAME_USER_MAX,
                                 user_max_quota_details.get_attribute_value(),
                                 abs_resource_name,
                                 abs_resource_name,
                                 user_max_attr_full_name,
                                 user_max_quota_details)

        group_max_attr_full_name = self.make_full_attribute_name(
                                        HighLevelAPI.ATTR_NAME_GROUP_MAX,
                                        abs_resource_name)
        group_max_quota_details = self.get_quota(
                                        entity=abs_resource_name,
                                        resource=group_max_attr_full_name)
        group_max_attr = NodeAttr(HighLevelAPI.ATTR_NAME_GROUP_MAX,
                                  group_max_quota_details.get_attribute_value(),
                                  abs_resource_name,
                                  abs_resource_name,
                                  group_max_attr_full_name,
                                  group_max_quota_details)
        
        return ResourceInfo(abs_resource_name,
                            resource_quota,
                            user_attr, user_max_attr, group_max_attr)
        
    def define_resource(self,
                        name,
                        total_quota,
                        user_quota,
                        user_max_quota,
                        group_max_quota):
        """
        Defines a resource globally known to QuotaDetails Holder.
        
        Returns the absolute name of the created resource. Note that this may
        be different from ``name``.
        
        The implementation maps a global resource to a QuotaDetails Holder __entity
        (so this is equivalent to a node in the high-level API but an extra
        check is made to ensure the resource is under 'system/resources').
        """
        ## TODO: Check total_quota is greater than the other quotas.
        ## TODO: Check user_max_quota >= user_quota

        # If the name is not in absolute form, make it so.
        # E.g. if it is 'pithos+' make it 'system/resources/pithos+'
        abs_resource_name = make_abs_resource_name(name)
                
        # Create the resource node
        self.create_node(node_name=abs_resource_name,
                         node_label='abs_resource_name')
        
        # Associate the node with the resource of the same
        # absolute name
        resource_quota = self.set_quota(entity=abs_resource_name,
            resource=abs_resource_name,
            quantity=total_quota,
            capacity=None, # Grow to infinity
            import_limit=None,
            export_limit=None,
            flags=0)
        
        user_attr = self.define_attribute_of_resource(
            abs_resource_name=abs_resource_name,
            attribute_name='user',
            attribute_value=user_quota,
            quantity=0,
            capacity=user_quota,
            import_limit=0,
            export_limit=0,
            flags=0)

        user_max_attr = self.define_attribute_of_resource(
            abs_resource_name=abs_resource_name,
            attribute_name='user_max',
            attribute_value=user_max_quota,
            quantity=0,
            capacity=user_max_quota,
            import_limit=0,
            export_limit=0,
            flags=0)

        group_max_attr = self.define_attribute_of_resource(
            abs_resource_name=abs_resource_name,
            attribute_name='group_max',
            attribute_value=group_max_quota,
            quantity=0,
            capacity=group_max_quota,
            import_limit=0,
            export_limit=0,
            flags=0)
        
        return ResourceInfo(abs_resource_name,
                           resource_quota,
                           user_attr, user_max_attr, group_max_attr)
        
    
    def define_attribute_of_resource(self,
                                     abs_resource_name,
                                     attribute_name,
                                     attribute_value,
                                     quantity,
                                     capacity,
                                     import_limit,
                                     export_limit,
                                     flags):
        """
        Defines an ``int`` attribute for global resource named
        ``global_resource_name``.
        
        The ``attribute_name`` must be simple, that is not an absolute name.
        
        Returns the computed name of the created attribute. Note that the
        computed name is not the same as ``attribute_name``.
        
        The implementation maps the attribute to a QuotaDetails Holder resource under
        the node (QuotaDetails Holder entity) named ``global_resource_name``. The
        respective value is defined via QuotaDetails Holder quotas. 
        """
        return self.__create_attribute_of_node_for_resource(
            node_name=abs_resource_name,
            node_label='abs_resource_name',
            resource_name=abs_resource_name,
            # `rdef` means we define for a Resource
            # The attribute name goes next
            # The absolute resource name goes next
            #    (will be added by the called method)
            attribute_name=attribute_name,
            attribute_value=attribute_value,
            quantity=quantity,
            capacity=capacity,
            import_limit=import_limit,
            export_limit=export_limit,
            flags=flags)

            
    
    def define_group(self, group_name):
        """
        Creates a new group under 'system/groups'.

        The ``group_name`` can either be an absolute name
        (e.g. 'system/groups/mygroup') or a relative name (e.g. 'mygroup').
        
        Returns the absolute group name of the created group. Note that this
        may be different from ``group_name``. 
        
        You must always use the __returned ``group_name`` as the
        most authoritative value instead of the one passed as a parameter.

        No further __resource assignment is done, you must use
        ``define_resource_of_group``.

        The implementation maps a group to a QuotaDetails Holder __entity.
        """
        # get name in absolute form
        abs_group_name = make_abs_group_name(group_name)
        
        # Create hierarchy on demand
        self.create_node(abs_group_name, 'abs_group_name')
        return GroupInfo(abs_group_name)
    

    
    def define_attribute_of_group_for_resource(self,
                                               abs_group_name,
                                               abs_resource_name,
                                               attribute_name,
                                               attribute_value,
                                               quantity,
                                               capacity,
                                               import_limit,
                                               export_limit,
                                               flags):
        check_abs_group_name(abs_group_name)
        check_abs_resource_name(abs_resource_name)
        
        return self.__create_attribute_of_node_for_resource(
            node_name=abs_group_name,
            node_label='abs_group_name',
            resource_name=abs_resource_name,
            attribute_name=attribute_name,
            attribute_value=attribute_value,
            quantity=quantity,
            capacity=capacity,
            import_limit=import_limit,
            export_limit=export_limit,
            flags=flags)
        

    def define_resource_of_group(self,
                                 group_name,
                                 resource_name,
                                 # How much the group gets in total
                                 resource_amount,
                                 # How much the group gives to the user
                                 user_quota,
                                 resource_amount_is_ondemand = False):
        """
        Defines a resource that a group provides to its users.
        """
        # TODO: Raise if it exists.
        # TODO: Provide a separate API for update
        abs_group_name = make_abs_group_name(group_name)
        abs_resource_name = make_abs_resource_name(resource_name)
        
        # Not implemented yet
        if resource_amount_is_ondemand:
            raise Exception(
                    "On demand group capacity is not supported for group %s" % (
                        group_name))
        
        if not self.resource_exists(abs_resource_name):
            raise Exception(
                "Cannot define resource '%s' for group '%s' because the global resource '%s' does not exist" %(
                    resource_name,
                    group_name,
                    abs_resource_name))
            
        if not self.node_exists(abs_group_name):
            raise Exception(
                "Cannot define resource '%s' for group '%s' because the group does not exist" %(
                    resource_name,
                    group_name))

        # Define the resource quotas for the group (initially empty)
        group_resource_quota = self.set_quota(
            entity=abs_group_name,
            resource=abs_resource_name,
            quantity=0,
            capacity=resource_amount,
            import_limit=None,
            export_limit=None,
            flags=0)
        # ... and do the quota_details transfer from the resource node
        self.issue_one_commission(
            target_entity=abs_group_name,
            source_entity=abs_resource_name,
            resource=abs_resource_name,
            quantity=resource_amount)
        
        # Other definitions
        user_attr = self.define_attribute_of_group_for_resource(
                            abs_group_name=abs_group_name,
                            abs_resource_name=abs_resource_name,
                            attribute_name=HighLevelAPI.ATTR_NAME_USER,
                            attribute_value=user_quota,
                            quantity=0,
                            capacity=user_quota,
                            import_limit=0,
                            export_limit=0,
                            flags=0)
        
        return GroupResourceInfo(abs_group_name,
                                 abs_resource_name,
                                 group_resource_quota,
                                 NodeAttr(HighLevelAPI.ATTR_NAME_USER,
                                          user_quota,
                                          abs_group_name,
                                          abs_resource_name,
                                          user_attr.full_name()
                                          ))


    #+++##########################################
    # Public, high-level API.
        #+++##########################################
    # Public, high-level API.
