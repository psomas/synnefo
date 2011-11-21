# Copyright 2011 GRNET S.A. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
#   1. Redistributions of source code must retain the above
#      copyright notice, this list of conditions and the following
#      disclaimer.
# 
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY GRNET S.A. ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL GRNET S.A OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# 
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of GRNET S.A.

from time import time
from sqlalchemy import Table, Integer, BigInteger, DECIMAL, Column, String, MetaData, ForeignKey
from sqlalchemy.types import Text
from sqlalchemy.schema import Index, Sequence
from sqlalchemy.sql import func, and_, or_, null, select, bindparam, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.engine.reflection import Inspector

from dbworker import DBWorker

ROOTNODE  = 0

( SERIAL, NODE, HASH, SIZE, SOURCE, MTIME, MUSER, CLUSTER ) = range(8)

inf = float('inf')


def strnextling(prefix):
    """Return the first unicode string
       greater than but not starting with given prefix.
       strnextling('hello') -> 'hellp'
    """
    if not prefix:
        ## all strings start with the null string,
        ## therefore we have to approximate strnextling('')
        ## with the last unicode character supported by python
        ## 0x10ffff for wide (32-bit unicode) python builds
        ## 0x00ffff for narrow (16-bit unicode) python builds
        ## We will not autodetect. 0xffff is safe enough.
        return unichr(0xffff)
    s = prefix[:-1]
    c = ord(prefix[-1])
    if c >= 0xffff:
        raise RuntimeError
    s += unichr(c+1)
    return s

def strprevling(prefix):
    """Return an approximation of the last unicode string
       less than but not starting with given prefix.
       strprevling(u'hello') -> u'helln\\xffff'
    """
    if not prefix:
        ## There is no prevling for the null string
        return prefix
    s = prefix[:-1]
    c = ord(prefix[-1])
    if c > 0:
        s += unichr(c-1) + unichr(0xffff)
    return s


_propnames = {
    'serial'    : 0,
    'node'      : 1,
    'hash'      : 2,
    'size'      : 3,
    'source'    : 4,
    'mtime'     : 5,
    'muser'     : 6,
    'cluster'   : 7,
}


class Node(DBWorker):
    """Nodes store path organization and have multiple versions.
       Versions store object history and have multiple attributes.
       Attributes store metadata.
    """
    
    # TODO: Provide an interface for included and excluded clusters.
    
    def __init__(self, **params):
        DBWorker.__init__(self, **params)
        metadata = MetaData()
        
        #create nodes table
        columns=[]
        columns.append(Column('node', Integer, primary_key=True))
        columns.append(Column('parent', Integer,
                              ForeignKey('nodes.node',
                                         ondelete='CASCADE',
                                         onupdate='CASCADE'),
                              autoincrement=False))
        path_length = 2048
        columns.append(Column('path', String(path_length), default='', nullable=False))
        self.nodes = Table('nodes', metadata, *columns, mysql_engine='InnoDB')
        
        #create policy table
        columns=[]
        columns.append(Column('node', Integer,
                              ForeignKey('nodes.node',
                                         ondelete='CASCADE',
                                         onupdate='CASCADE'),
                              primary_key=True))
        columns.append(Column('key', String(255), primary_key=True))
        columns.append(Column('value', String(255)))
        self.policies = Table('policy', metadata, *columns, mysql_engine='InnoDB')
        
        #create statistics table
        columns=[]
        columns.append(Column('node', Integer,
                              ForeignKey('nodes.node',
                                         ondelete='CASCADE',
                                         onupdate='CASCADE'),
                              primary_key=True))
        columns.append(Column('population', Integer, nullable=False, default=0))
        columns.append(Column('size', BigInteger, nullable=False, default=0))
        columns.append(Column('mtime', DECIMAL(precision=16, scale=6)))
        columns.append(Column('cluster', Integer, nullable=False, default=0,
                              primary_key=True, autoincrement=False))
        self.statistics = Table('statistics', metadata, *columns, mysql_engine='InnoDB')
        
        #create versions table
        columns=[]
        columns.append(Column('serial', Integer, primary_key=True))
        columns.append(Column('node', Integer,
                              ForeignKey('nodes.node',
                                         ondelete='CASCADE',
                                         onupdate='CASCADE')))
        columns.append(Column('hash', String(255)))
        columns.append(Column('size', BigInteger, nullable=False, default=0))
        columns.append(Column('source', Integer))
        columns.append(Column('mtime', DECIMAL(precision=16, scale=6)))
        columns.append(Column('muser', String(255), nullable=False, default=''))
        columns.append(Column('cluster', Integer, nullable=False, default=0))
        self.versions = Table('versions', metadata, *columns, mysql_engine='InnoDB')
        Index('idx_versions_node_mtime', self.versions.c.node,
              self.versions.c.mtime)
        
        #create attributes table
        columns = []
        columns.append(Column('serial', Integer,
                              ForeignKey('versions.serial',
                                         ondelete='CASCADE',
                                         onupdate='CASCADE'),
                              primary_key=True))
        columns.append(Column('key', String(255), primary_key=True))
        columns.append(Column('value', String(255)))
        self.attributes = Table('attributes', metadata, *columns, mysql_engine='InnoDB')
        
        metadata.create_all(self.engine)
        
        # the following code creates an index of specific length
        # this can be accompliced in sqlalchemy >= 0.7.3
        # providing mysql_length option during index creation
        insp = Inspector.from_engine(self.engine)
        indexes = [elem['name'] for elem in insp.get_indexes('nodes')]
        if 'idx_nodes_path' not in indexes:
            explicit_length = '(%s)' %path_length if self.engine.name == 'mysql' else ''
            s = text('CREATE INDEX idx_nodes_path ON nodes (path%s)' %explicit_length)
            self.conn.execute(s).close()
        
        s = self.nodes.select().where(and_(self.nodes.c.node == ROOTNODE,
                                           self.nodes.c.parent == ROOTNODE))
        rp = self.conn.execute(s)
        r = rp.fetchone()
        rp.close()
        if not r:
            s = self.nodes.insert().values(node=ROOTNODE, parent=ROOTNODE)
            self.conn.execute(s)
    
    def node_create(self, parent, path):
        """Create a new node from the given properties.
           Return the node identifier of the new node.
        """
        #TODO catch IntegrityError?
        s = self.nodes.insert().values(parent=parent, path=path)
        r = self.conn.execute(s)
        inserted_primary_key = r.inserted_primary_key[0]
        r.close()
        return inserted_primary_key
    
    def node_lookup(self, path):
        """Lookup the current node of the given path.
           Return None if the path is not found.
        """
        
        s = select([self.nodes.c.node], self.nodes.c.path.like(path))
        r = self.conn.execute(s)
        row = r.fetchone()
        r.close()
        if row:
            return row[0]
        return None
    
    def node_get_properties(self, node):
        """Return the node's (parent, path).
           Return None if the node is not found.
        """
        
        s = select([self.nodes.c.parent, self.nodes.c.path])
        s = s.where(self.nodes.c.node == node)
        r = self.conn.execute(s)
        l = r.fetchone()
        r.close()
        return l
    
    def node_get_versions(self, node, keys=(), propnames=_propnames):
        """Return the properties of all versions at node.
           If keys is empty, return all properties in the order
           (serial, node, size, source, mtime, muser, cluster).
        """
        
        s = select([self.versions.c.serial,
                    self.versions.c.node,
                    self.versions.c.hash,
                    self.versions.c.size,
                    self.versions.c.source,
                    self.versions.c.mtime,
                    self.versions.c.muser,
                    self.versions.c.cluster], self.versions.c.node == node)
        s = s.order_by(self.versions.c.serial)
        r = self.conn.execute(s)
        rows = r.fetchall()
        r.close()
        if not rows:
            return rows
        
        if not keys:
            return rows
        
        return [[p[propnames[k]] for k in keys if k in propnames] for p in rows]
    
    def node_count_children(self, node):
        """Return node's child count."""
        
        s = select([func.count(self.nodes.c.node)])
        s = s.where(and_(self.nodes.c.parent == node,
                         self.nodes.c.node != ROOTNODE))
        r = self.conn.execute(s)
        row = r.fetchone()
        r.close()
        return row[0]
    
    def node_purge_children(self, parent, before=inf, cluster=0):
        """Delete all versions with the specified
           parent and cluster, and return
           the hashes of versions deleted.
           Clears out nodes with no remaining versions.
        """
        #update statistics
        c1 = select([self.nodes.c.node],
            self.nodes.c.parent == parent)
        where_clause = and_(self.versions.c.node.in_(c1),
                            self.versions.c.cluster == cluster)
        s = select([func.count(self.versions.c.serial),
                    func.sum(self.versions.c.size)])
        s = s.where(where_clause)
        if before != inf:
            s = s.where(self.versions.c.mtime <= before)
        r = self.conn.execute(s)
        row = r.fetchone()
        r.close()
        if not row:
            return ()
        nr, size = row[0], -row[1] if row[1] else 0
        mtime = time()
        self.statistics_update(parent, -nr, size, mtime, cluster)
        self.statistics_update_ancestors(parent, -nr, size, mtime, cluster)
        
        s = select([self.versions.c.hash])
        s = s.where(where_clause)
        r = self.conn.execute(s)
        hashes = [row[0] for row in r.fetchall()]
        r.close()
        
        #delete versions
        s = self.versions.delete().where(where_clause)
        r = self.conn.execute(s)
        r.close()
        
        #delete nodes
        s = select([self.nodes.c.node],
            and_(self.nodes.c.parent == parent,
                 select([func.count(self.versions.c.serial)],
                    self.versions.c.node == self.nodes.c.node).as_scalar() == 0))
        rp = self.conn.execute(s)
        nodes = [r[0] for r in rp.fetchall()]
        rp.close()
        s = self.nodes.delete().where(self.nodes.c.node.in_(nodes))
        self.conn.execute(s).close()
        
        return hashes
    
    def node_purge(self, node, before=inf, cluster=0):
        """Delete all versions with the specified
           node and cluster, and return
           the hashes of versions deleted.
           Clears out the node if it has no remaining versions.
        """
        
        #update statistics
        s = select([func.count(self.versions.c.serial),
                    func.sum(self.versions.c.size)])
        where_clause = and_(self.versions.c.node == node,
                         self.versions.c.cluster == cluster)
        s = s.where(where_clause)
        if before != inf:
            s = s.where(self.versions.c.mtime <= before)
        r = self.conn.execute(s)
        row = r.fetchone()
        nr, size = row[0], row[1]
        r.close()
        if not nr:
            return ()
        mtime = time()
        self.statistics_update_ancestors(node, -nr, -size, mtime, cluster)
        
        s = select([self.versions.c.hash])
        s = s.where(where_clause)
        r = self.conn.execute(s)
        hashes = [r[0] for r in r.fetchall()]
        r.close()
        
        #delete versions
        s = self.versions.delete().where(where_clause)
        r = self.conn.execute(s)
        r.close()
        
        #delete nodes
        s = select([self.nodes.c.node],
            and_(self.nodes.c.node == node,
                 select([func.count(self.versions.c.serial)],
                    self.versions.c.node == self.nodes.c.node).as_scalar() == 0))
        r = self.conn.execute(s)
        nodes = r.fetchall()
        r.close()
        s = self.nodes.delete().where(self.nodes.c.node.in_(nodes))
        self.conn.execute(s).close()
        
        return hashes
    
    def node_remove(self, node):
        """Remove the node specified.
           Return false if the node has children or is not found.
        """
        
        if self.node_count_children(node):
            return False
        
        mtime = time()
        s = select([func.count(self.versions.c.serial),
                    func.sum(self.versions.c.size),
                    self.versions.c.cluster])
        s = s.where(self.versions.c.node == node)
        s = s.group_by(self.versions.c.cluster)
        r = self.conn.execute(s)
        for population, size, cluster in r.fetchall():
            self.statistics_update_ancestors(node, -population, -size, mtime, cluster)
        r.close()
        
        s = self.nodes.delete().where(self.nodes.c.node == node)
        self.conn.execute(s).close()
        return True
    
    def policy_get(self, node):
        s = select([self.policies.c.key, self.policies.c.value],
            self.policies.c.node==node)
        r = self.conn.execute(s)
        d = dict(r.fetchall())
        r.close()
        return d
    
    def policy_set(self, node, policy):
        #insert or replace
        for k, v in policy.iteritems():
            s = self.policies.update().where(and_(self.policies.c.node == node,
                                                  self.policies.c.key == k))
            s = s.values(value = v)
            rp = self.conn.execute(s)
            rp.close()
            if rp.rowcount == 0:
                s = self.policies.insert()
                values = {'node':node, 'key':k, 'value':v}
                r = self.conn.execute(s, values)
                r.close()
    
    def statistics_get(self, node, cluster=0):
        """Return population, total size and last mtime
           for all versions under node that belong to the cluster.
        """
        
        s = select([self.statistics.c.population,
                    self.statistics.c.size,
                    self.statistics.c.mtime])
        s = s.where(and_(self.statistics.c.node == node,
                         self.statistics.c.cluster == cluster))
        r = self.conn.execute(s)
        row = r.fetchone()
        r.close()
        return row
    
    def statistics_update(self, node, population, size, mtime, cluster=0):
        """Update the statistics of the given node.
           Statistics keep track the population, total
           size of objects and mtime in the node's namespace.
           May be zero or positive or negative numbers.
        """
        s = select([self.statistics.c.population, self.statistics.c.size],
            and_(self.statistics.c.node == node,
                 self.statistics.c.cluster == cluster))
        rp = self.conn.execute(s)
        r = rp.fetchone()
        rp.close()
        if not r:
            prepopulation, presize = (0, 0)
        else:
            prepopulation, presize = r
        population += prepopulation
        size += presize
        
        #insert or replace
        #TODO better upsert
        u = self.statistics.update().where(and_(self.statistics.c.node==node,
                                           self.statistics.c.cluster==cluster))
        u = u.values(population=population, size=size, mtime=mtime)
        rp = self.conn.execute(u)
        rp.close()
        if rp.rowcount == 0:
            ins = self.statistics.insert()
            ins = ins.values(node=node, population=population, size=size,
                             mtime=mtime, cluster=cluster)
            self.conn.execute(ins).close()
    
    def statistics_update_ancestors(self, node, population, size, mtime, cluster=0):
        """Update the statistics of the given node's parent.
           Then recursively update all parents up to the root.
           Population is not recursive.
        """
        
        while True:
            if node == ROOTNODE:
                break
            props = self.node_get_properties(node)
            if props is None:
                break
            parent, path = props
            self.statistics_update(parent, population, size, mtime, cluster)
            node = parent
            population = 0 # Population isn't recursive
    
    def statistics_latest(self, node, before=inf, except_cluster=0):
        """Return population, total size and last mtime
           for all latest versions under node that
           do not belong to the cluster.
        """
        
        # The node.
        props = self.node_get_properties(node)
        if props is None:
            return None
        parent, path = props
        
        # The latest version.
        s = select([self.versions.c.serial,
                    self.versions.c.node,
                    self.versions.c.hash,
                    self.versions.c.size,
                    self.versions.c.source,
                    self.versions.c.mtime,
                    self.versions.c.muser,
                    self.versions.c.cluster])
        filtered = select([func.max(self.versions.c.serial)],
                            self.versions.c.node == node)
        if before != inf:
            filtered = filtered.where(self.versions.c.mtime < before)
        s = s.where(and_(self.versions.c.cluster != except_cluster,
                         self.versions.c.serial == filtered))
        r = self.conn.execute(s)
        props = r.fetchone()
        r.close()
        if not props:
            return None
        mtime = props[MTIME]
        
        # First level, just under node (get population).
        v = self.versions.alias('v')
        s = select([func.count(v.c.serial),
                    func.sum(v.c.size),
                    func.max(v.c.mtime)])
        c1 = select([func.max(self.versions.c.serial)])
        if before != inf:
            c1 = c1.where(self.versions.c.mtime < before)
        c2 = select([self.nodes.c.node], self.nodes.c.parent == node)
        s = s.where(and_(v.c.serial == c1.where(self.versions.c.node == v.c.node),
                         v.c.cluster != except_cluster,
                         v.c.node.in_(c2)))
        rp = self.conn.execute(s)
        r = rp.fetchone()
        rp.close()
        if not r:
            return None
        count = r[0]
        mtime = max(mtime, r[2])
        if count == 0:
            return (0, 0, mtime)
        
        # All children (get size and mtime).
        # XXX: This is why the full path is stored.
        s = select([func.count(v.c.serial),
                    func.sum(v.c.size),
                    func.max(v.c.mtime)])
        c1 = select([func.max(self.versions.c.serial)],
            self.versions.c.node == v.c.node)
        if before != inf:
            c1 = c1.where(self.versions.c.mtime < before)
        c2 = select([self.nodes.c.node], self.nodes.c.path.like(path + '%'))
        s = s.where(and_(v.c.serial == c1,
                         v.c.cluster != except_cluster,
                         v.c.node.in_(c2)))
        rp = self.conn.execute(s)
        r = rp.fetchone()
        rp.close()
        if not r:
            return None
        size = r[1] - props[SIZE]
        mtime = max(mtime, r[2])
        return (count, size, mtime)
    
    def version_create(self, node, hash, size, source, muser, cluster=0):
        """Create a new version from the given properties.
           Return the (serial, mtime) of the new version.
        """
        
        mtime = time()
        s = self.versions.insert().values(node=node, hash=hash, size=size, source=source,
                                          mtime=mtime, muser=muser, cluster=cluster)
        serial = self.conn.execute(s).inserted_primary_key[0]
        self.statistics_update_ancestors(node, 1, size, mtime, cluster)
        return serial, mtime
    
    def version_lookup(self, node, before=inf, cluster=0):
        """Lookup the current version of the given node.
           Return a list with its properties:
           (serial, node, hash, size, source, mtime, muser, cluster)
           or None if the current version is not found in the given cluster.
        """
        
        v = self.versions.alias('v')
        s = select([v.c.serial, v.c.node, v.c.hash, v.c.size,
                    v.c.source, v.c.mtime, v.c.muser, v.c.cluster])
        c = select([func.max(self.versions.c.serial)],
            self.versions.c.node == node)
        if before != inf:
            c = c.where(self.versions.c.mtime < before)
        s = s.where(and_(v.c.serial == c,
                         v.c.cluster == cluster))
        r = self.conn.execute(s)
        props = r.fetchone()
        r.close()
        if props:
            return props
        return None
    
    def version_get_properties(self, serial, keys=(), propnames=_propnames):
        """Return a sequence of values for the properties of
           the version specified by serial and the keys, in the order given.
           If keys is empty, return all properties in the order
           (serial, node, hash, size, source, mtime, muser, cluster).
        """
        
        v = self.versions.alias()
        s = select([v.c.serial, v.c.node, v.c.hash, v.c.size,
                    v.c.source, v.c.mtime, v.c.muser, v.c.cluster], v.c.serial == serial)
        rp = self.conn.execute(s)
        r = rp.fetchone()
        rp.close()
        if r is None:
            return r
        
        if not keys:
            return r
        return [r[propnames[k]] for k in keys if k in propnames]
    
    def version_recluster(self, serial, cluster):
        """Move the version into another cluster."""
        
        props = self.version_get_properties(serial)
        if not props:
            return
        node = props[NODE]
        size = props[SIZE]
        oldcluster = props[CLUSTER]
        if cluster == oldcluster:
            return
        
        mtime = time()
        self.statistics_update_ancestors(node, -1, -size, mtime, oldcluster)
        self.statistics_update_ancestors(node, 1, size, mtime, cluster)
        
        s = self.versions.update()
        s = s.where(self.versions.c.serial == serial)
        s = s.values(cluster = cluster)
        self.conn.execute(s).close()
    
    def version_remove(self, serial):
        """Remove the serial specified."""
        
        props = self.node_get_properties(serial)
        if not props:
            return
        node = props[NODE]
        size = props[SIZE]
        cluster = props[CLUSTER]
        
        mtime = time()
        self.statistics_update_ancestors(node, -1, -size, mtime, cluster)
        
        s = self.versions.delete().where(self.versions.c.serial == serial)
        self.conn.execute(s).close()
        return True
    
    def attribute_get(self, serial, keys=()):
        """Return a list of (key, value) pairs of the version specified by serial.
           If keys is empty, return all attributes.
           Othwerise, return only those specified.
        """
        
        if keys:
            attrs = self.attributes.alias()
            s = select([attrs.c.key, attrs.c.value])
            s = s.where(and_(attrs.c.key.in_(keys),
                             attrs.c.serial == serial))
        else:
            attrs = self.attributes.alias()
            s = select([attrs.c.key, attrs.c.value])
            s = s.where(attrs.c.serial == serial)
        r = self.conn.execute(s)
        l = r.fetchall()
        r.close()
        return l
    
    def attribute_set(self, serial, items):
        """Set the attributes of the version specified by serial.
           Receive attributes as an iterable of (key, value) pairs.
        """
        #insert or replace
        #TODO better upsert
        for k, v in items:
            s = self.attributes.update()
            s = s.where(and_(self.attributes.c.serial == serial,
                             self.attributes.c.key == k))
            s = s.values(value = v)
            rp = self.conn.execute(s)
            rp.close()
            if rp.rowcount == 0:
                s = self.attributes.insert()
                s = s.values(serial=serial, key=k, value=v)
                self.conn.execute(s).close()
    
    def attribute_del(self, serial, keys=()):
        """Delete attributes of the version specified by serial.
           If keys is empty, delete all attributes.
           Otherwise delete those specified.
        """
        
        if keys:
            #TODO more efficient way to do this?
            for key in keys:
                s = self.attributes.delete()
                s = s.where(and_(self.attributes.c.serial == serial,
                                 self.attributes.c.key == key))
                self.conn.execute(s).close()
        else:
            s = self.attributes.delete()
            s = s.where(self.attributes.c.serial == serial)
            self.conn.execute(s).close()
    
    def attribute_copy(self, source, dest):
        s = select([dest, self.attributes.c.key, self.attributes.c.value],
            self.attributes.c.serial == source)
        rp = self.conn.execute(s)
        attributes = rp.fetchall()
        rp.close()
        for dest, k, v in attributes:
            #insert or replace
            s = self.attributes.update().where(and_(
                self.attributes.c.serial == dest,
                self.attributes.c.key == k))
            rp = self.conn.execute(s, value=v)
            rp.close()
            if rp.rowcount == 0:
                s = self.attributes.insert()
                values = {'serial':dest, 'key':k, 'value':v}
                self.conn.execute(s, values).close()
    
    def latest_attribute_keys(self, parent, before=inf, except_cluster=0, pathq=[]):
        """Return a list with all keys pairs defined
           for all latest versions under parent that
           do not belong to the cluster.
        """
        
        # TODO: Use another table to store before=inf results.
        a = self.attributes.alias('a')
        v = self.versions.alias('v')
        n = self.nodes.alias('n')
        s = select([a.c.key]).distinct()
        filtered = select([func.max(self.versions.c.serial)])
        if before != inf:
            filtered = filtered.where(self.versions.c.mtime < before)
        s = s.where(v.c.serial == filtered.where(self.versions.c.node == v.c.node))
        s = s.where(v.c.cluster != except_cluster)
        s = s.where(v.c.node.in_(select([self.nodes.c.node],
            self.nodes.c.parent == parent)))
        s = s.where(a.c.serial == v.c.serial)
        s = s.where(n.c.node == v.c.node)
        conj = []
        for x in pathq:
            conj.append(n.c.path.like(x + '%'))
        if conj:
            s = s.where(or_(*conj))
        rp = self.conn.execute(s)
        rows = rp.fetchall()
        rp.close()
        return [r[0] for r in rows]
    
    def latest_version_list(self, parent, prefix='', delimiter=None,
                            start='', limit=10000, before=inf,
                            except_cluster=0, pathq=[], filterq=None):
        """Return a (list of (path, serial) tuples, list of common prefixes)
           for the current versions of the paths with the given parent,
           matching the following criteria.
           
           The property tuple for a version is returned if all
           of these conditions are true:
                
                a. parent matches
                
                b. path > start
                
                c. path starts with prefix (and paths in pathq)
                
                d. version is the max up to before
                
                e. version is not in cluster
                
                f. the path does not have the delimiter occuring
                   after the prefix, or ends with the delimiter
                
                g. serial matches the attribute filter query.
                   
                   A filter query is a comma-separated list of
                   terms in one of these three forms:
                   
                   key
                       an attribute with this key must exist
                   
                   !key
                       an attribute with this key must not exist
                   
                   key ?op value
                       the attribute with this key satisfies the value
                       where ?op is one of ==, != <=, >=, <, >.
           
           The list of common prefixes includes the prefixes
           matching up to the first delimiter after prefix,
           and are reported only once, as "virtual directories".
           The delimiter is included in the prefixes.
           
           If arguments are None, then the corresponding matching rule
           will always match.
           
           Limit applies to the first list of tuples returned.
        """
        
        if not start or start < prefix:
            start = strprevling(prefix)
        nextling = strnextling(prefix)
        
        a = self.attributes.alias('a')
        v = self.versions.alias('v')
        n = self.nodes.alias('n')
        s = select([n.c.path, v.c.serial]).distinct()
        filtered = select([func.max(self.versions.c.serial)])
        if before != inf:
            filtered = filtered.where(self.versions.c.mtime < before)
        s = s.where(v.c.serial == filtered.where(self.versions.c.node == v.c.node))
        s = s.where(v.c.cluster != except_cluster)
        s = s.where(v.c.node.in_(select([self.nodes.c.node],
            self.nodes.c.parent == parent)))
        if filterq:
            s = s.where(a.c.serial == v.c.serial)
        
        s = s.where(n.c.node == v.c.node)
        s = s.where(and_(n.c.path > bindparam('start'), n.c.path < nextling))
        conj = []
        for x in pathq:
            conj.append(n.c.path.like(x + '%'))
        
        if conj:
            s = s.where(or_(*conj))
        
        if filterq:
            s = s.where(a.c.key.in_(filterq.split(',')))
        
        s = s.order_by(n.c.path)
        
        if not delimiter:
            s = s.limit(limit)
            rp = self.conn.execute(s, start=start)
            r = rp.fetchall()
            rp.close()
            return r, ()
        
        pfz = len(prefix)
        dz = len(delimiter)
        count = 0
        prefixes = []
        pappend = prefixes.append
        matches = []
        mappend = matches.append
        
        rp = self.conn.execute(s, start=start)
        while True:
            props = rp.fetchone()
            if props is None:
                break
            path, serial = props
            idx = path.find(delimiter, pfz)
            
            if idx < 0:
                mappend(props)
                count += 1
                if count >= limit:
                    break
                continue
            
            if idx + dz == len(path):
                mappend(props)
                count += 1
                continue # Get one more, in case there is a path.
            pf = path[:idx + dz]
            pappend(pf)
            if count >= limit: 
                break
            
            rp = self.conn.execute(s, start=strnextling(pf)) # New start.
        rp.close()
        
        return matches, prefixes
