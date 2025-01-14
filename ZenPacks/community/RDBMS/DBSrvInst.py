################################################################################
#
# This program is part of the RDBMS Zenpack for Zenoss.
# Copyright (C) 2009-2012 Egor Puzanov.
#
# This program can be used under the GNU General Public License version 2
# You can find full information here: http://www.zenoss.com/oss
#
################################################################################

__doc__="""DBSrvInst

DBSrvInst is a DBSrvInst

$Id: DBSrvInst.py,v 1.4 2012/03/31 22:09:16 egor Exp $"""

__version__ = "$Revision: 1.4 $"[11:-2]

from Globals import InitializeClass, DTMLFile
from AccessControl import ClassSecurityInfo
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from Products.ZenModel.ZenossSecurity import *
from Products.ZenUtils.Utils import prepId
from Products.ZenRelations.RelSchema import *
from Products.ZenWidgets import messaging

from Products.ZenModel.DeviceComponent import DeviceComponent
from Products.ZenModel.MEProduct import MEProduct

def manage_addDBSrvInst(context, id, userCreated, REQUEST=None):
    """make a database"""
    dbsiid = prepId(id)
    dbsi = DBSrvInst(dbsiid)
    context._setObject(dbsiid, dbsi)
    dbsi = context._getOb(dbsiid)
    dbsi.dbsiname = id
    if userCreated: dbsi.setUserCreateFlag()
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(context.absolute_url()+'/manage_main') 

addDBSrvInst = DTMLFile('dtml/addDBSrvInst',globals())

class DBSrvInst(ZenPackPersistence, DeviceComponent, MEProduct):
    """
    DBSrvInst object
    """

    ZENPACKID = 'ZenPacks.community.RDBMS'

    portal_type = meta_type = 'DBSrvInst'

    manage_editDBSrvInstForm = DTMLFile('dtml/manageDBSrvInst',globals())

    isUserCreatedFlag = False
    snmpindex = ""
    dbsiname = ""
    contact = ""
    procRegex = ""
    monitorProc = False
    status = 0

    statusConversions = [
                'Up:0',
                'Down:1',
                ]

    statusmap ={0: ('green', 0, 'Up'),
                1: ('red', 5, 'Down'),
                }

    _properties = (
        {'id':'procRegex', 'type':'string', 'mode':'w'},
        {'id':'monitorProc', 'type':'boolean', 'mode':'w'},
        {'id':'installDate', 'type':'date', 'mode':''},
        {'id':'snmpindex', 'type':'string', 'mode':'w'},
        {'id':'dbsiname', 'type':'string', 'mode':'w'},
        {'id':'contact', 'type':'string', 'mode':'w'},
        {'id':'status', 'type':'int', 'mode':'w'},
        )

    _relations = MEProduct._relations + (
        ("os", ToOne(ToManyCont, "Products.ZenModel.OperatingSystem", "softwaredbsrvinstances")),
        ("databases", ToMany(ToOne, "ZenPacks.community.RDBMS.Database", "dbsrvinstance")),
        )

    factory_type_information = (
        {
            'id'             : 'DBSrvInst',
            'meta_type'      : 'DBSrvInst',
            'description'    : """Arbitrary device grouping class""",
            'icon'           : 'FileSystem_icon.gif',
            'product'        : 'RDBMS',
            'factory'        : 'manage_addDBSrvInst',
            'immediate_view' : 'viewDBSrvInst',
            'actions'        :
            (
                { 'id'            : 'status'
                , 'name'          : 'Status'
                , 'action'        : 'viewDBSrvInst'
                , 'permissions'   : (ZEN_VIEW,)
                },
                { 'id'            : 'databases'
                , 'name'          : 'Databases'
                , 'action'        : 'viewDBSrvInstDatabases'
                , 'permissions'   : (ZEN_VIEW,)
                },
                { 'id'            : 'events'
                , 'name'          : 'Events'
                , 'action'        : 'viewEvents'
                , 'permissions'   : (ZEN_VIEW,)
                },
                { 'id'            : 'perfConf'
                , 'name'          : 'Template'
                , 'action'        : 'objTemplates'
                , 'permissions'   : (ZEN_CHANGE_DEVICE,)
                },
                { 'id'            : 'viewHistory'
                , 'name'          : 'Modifications'
                , 'action'        : 'viewHistory'
                , 'permissions'   : (ZEN_VIEW_MODIFICATIONS,)
                },
            )
          },
        )


    security = ClassSecurityInfo()

    def __init__(self, id, title=""):
        MEProduct.__init__(self, id, title)

    security.declareProtected('Change Device', 'setProduct')
    def setProduct(self, productName,  manufacturer="Unknown", 
                    newProductName="", REQUEST=None, **kwargs):
        """Set the product class of this software.
        """
        if not manufacturer: manufacturer = "Unknown"
        if newProductName: productName = newProductName
        prodobj = self.getDmdRoot("Manufacturers").createSoftwareProduct(
                                    productName, manufacturer, **kwargs)
        self.productClass.addRelation(prodobj)
        if REQUEST:
            messaging.IMessageSender(self).sendToBrowser(
                'Product Set',
                ("Set Manufacturer %s and Product %s."
                                    % (manufacturer, productName))
            )
            return self.callZenScreen(REQUEST)

    def setProductKey(self, prodKey, manufacturer=None):
        """Set the product class of this software by its productKey.
        """
        if prodKey:
            # Store these so we can return the proper value from getProductKey
            self._prodKey = prodKey
            self._manufacturer = manufacturer

            if manufacturer is None:
                manufacturer = 'Unknown'

            manufs = self.getDmdRoot("Manufacturers")
            prodobj = manufs.createSoftwareProduct(prodKey, manufacturer)
            self.productClass.addRelation(prodobj)
        else:
            self.productClass.removeRelation()

    def name(self):
        """Return the name of this software (from its softwareClass)
        """
        pclass = self.productClass()
        if pclass: return pclass.name
        return ""

    def version(self):
        """Return the version of this software (from its softwareClass)
        """
        pclass = self.productClass()
        if pclass: return pclass.version
        return ""

    def build(self):
        """Return the build of this software (from its softwareClass)
        """
        pclass = self.productClass()
        if pclass: return pclass.build
        return ""

    def setUserCreateFlag(self):
        """
        Sets self.isUserCreatedFlag to True.  This indicated that the
        component was created by a user rather than via modelling.
        """
        self.isUserCreatedFlag = True

    def isUserCreated(self):
        """
        Returns the value of isUserCreated.  See setUserCreatedFlag() above.
        """
        return self.isUserCreatedFlag

    def device(self):
        """
        Return our device object for DeviceResultInt.
        """
        os = self.os()
        if os: return os.device()

    def manage_deleteComponent(self, REQUEST=None):
        """
        Delete OSComponent
        """
        url = None
        if REQUEST is not None:
            url = self.device().os.absolute_url()
        self.getPrimaryParent()._delObject(self.id)
        '''
        eventDict = {
            'eventClass': Change_Remove,
            'device': self.device().id,
            'component': self.id or '',
            'summary': 'Deleted by user: %s' % 'user',
            'severity': Event.Info,
            }
        self.dmd.ZenEventManager.sendEvent(eventDict)
        '''
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(url)

    def manage_updateComponent(self, datamap, REQUEST=None):
        """
        Update OSComponent
        """
        url = None
        if REQUEST is not None:
            url = self.device().os.absolute_url()
        self.getPrimaryParent()._updateObject(self, datamap)
        '''
        eventDict = {
            'eventClass': Change_Set,
            'device': self.device().id,
            'component': self.id or '',
            'summary': 'Updated by user: %s' % 'user',
            'severity': Event.Info,
            }
        self.dmd.ZenEventManager.sendEvent(eventDict)
        '''
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(url)

    def getPrettyLink(self):
        """
        Gets a link to this object, plus an icon
        """
        template = ("<a href='%s' class='prettylink'>"
                    "<div class='device-icon-container'> "
                    "<img class='device-icon' src='%s'/> "
                    "</div>%s</a>")
        icon = self.getIconPath()
        href = self.getPrimaryUrlPath()
        name = self.titleOrId()
        return template % (href, icon, name)

    def viewName(self): 
        """
        Return the name of a DB Server Instance
        """
        return self.dbsiname
    name = viewName

    security.declareProtected(ZEN_CHANGE_DEVICE, 'convertStatus')
    def convertStatus(self, status):
        """
        Convert status to the status string
        """
        return self.statusmap.get(status, ('grey', 3, 'Other'))[2]

    security.declareProtected(ZEN_CHANGE_DEVICE, 'getStatus')
    def getStatus(self, statClass=None):
        """
        Return the status number for this component of class statClass.
        """
        if not self.monitored() \
            or not self.device() \
            or not self.device().monitorDevice(): return 0
        return self.status

    def getStatusImgSrc(self, status=None):
        """
        Return the img source for a status number
        """
        if status is None: status = self.getStatus()
        src = self.statusmap.get(status, ('grey', 3, 'Other'))[0]
        return '/zport/dmd/img/%s_dot.png' % src

    def statusDot(self, status=None):
        """
        Return the img source for a status number
        Return the Dot Color based on maximal severity
        """
        if status is None: status = self.getStatus()
        return self.statusmap.get(status, ('grey', 3, 'Other'))[0]

    def statusString(self, status=None):
        """
        Return the status string
        """
        if status is None: status = self.getStatus()
        return self.getStatusString(status)

    def getRRDTemplates(self):
        """
        Return the RRD Templates list
        """
        templates = []
        for tmplName in (self.__class__.__name__, self.meta_type):
            template = self.getRRDTemplateByName(tmplName)
            if template is None: continue
            templates.append(template)
            break
        return templates

    def manage_editDBSrvInst(self, monitor=False, dbsiname=None, REQUEST=None):
        """
        Edit a DB Server Instance from a web page.
        """
        if dbsiname:
            self.dbsiname = dbsiname

        self.monitor = monitor
        self.index_object()

        if REQUEST:
            REQUEST['message'] = "DB Server Instance updated"
            messaging.IMessageSender(self).sendToBrowser(
                'DB Server Instance Updated',
                'DB Server Instance %s was updated.' % dbsiname
            )
            return self.callZenScreen(REQUEST)

InitializeClass(DBSrvInst)
