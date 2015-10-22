__author__ = 'Sol'
CONTEXT_FIELD_DOCSTR=dict()

CONTEXT_FIELD_DOCSTR['lcName'] = u"Contains a zero-terminated context name string."

CONTEXT_FIELD_DOCSTR['lcOptions']=u"Specifies options for the context. " \
                                  u"These options can be combined by using the " \
                                  u"bitwise OR operator. The lcOptions field " \
                                  u"can be any combination of the values " \
                                  u"defined in table 7.11. Specifying options " \
                                  u"that are unsupported in a particular " \
                                  u"implementation will cause WTOpen to fail."

CONTEXT_FIELD_DOCSTR['lcStatus']=u"Specifies current status conditions for the " \
                                 u"context. " \
                                 u"These conditions can be combined by using " \
                                 u"the bitwise OR opera­tor. The lcStatus " \
                                 u"field can be any combination of the " \
                                 u"values defined in table 7.12."

CONTEXT_FIELD_DOCSTR['lcLocks']=u"Specifies which attributes of the context " \
                                u"the application wishes to be locked. " \
                                u"Lock conditions specify attributes of the " \
                                u"context that cannot be changed once the " \
                                u"context has been opened (calls to " \
                                u"WTConfig will have no effect on the locked " \
                                u"attributes). The lock conditions can be " \
                                u"combined by using the bitwise OR operator. " \
                                u"The lcLocks field can be any combination of" \
                                u" the values de­fined in table 7.13. Locks " \
                                u"can only be changed by the task or process " \
                                u"that owns the context."

CONTEXT_FIELD_DOCSTR['lcMsgBase']=u"Specifies the range of message numbers " \
                                  u"that will be used for re­porting" \
                                  u" the activity of the context. " \
                                  u"See the message descrip­tions in section 6."

CONTEXT_FIELD_DOCSTR['lcDevice']=u"Specifies the device whose input the " \
                                 u"context processes."

CONTEXT_FIELD_DOCSTR['lcPktRate']=u"Specifies the desired packet " \
                                  u"report rate in Hertz. " \
                                  u"Once the con­text is opened, this field " \
                                  u"will contain the actual report rate."

CONTEXT_FIELD_DOCSTR['lcPktData']=u"Specifies which optional data items will " \
                                  u"be in packets re­turned from the context." \
                                  u"Requesting unsupported data items will " \
                                  u"cause WTOpen to fail."

CONTEXT_FIELD_DOCSTR['lcPktMode']=u"Specifies whether the packet data items " \
                                  u"will be returned in abso­lute or " \
                                  u"relative mode." \
                                  u" If the item's bit is set in this field, " \
                                  u"the item will be returned in relative mode. " \
                                  u"Bits in this field for items not selected " \
                                  u"in the lcPktData field will be ignored. " \
                                  u"Bits for data items that only allow one " \
                                  u"mode (such as the serial number) will " \
                                  u"also be ignored."

CONTEXT_FIELD_DOCSTR['lcMoveMask']=u"Specifies which packet data items can " \
                                   u"generate move events in the context." \
                                   u" Bits for items that are not part of the" \
                                   u" packet def­ini­tion in the lcPktData" \
                                   u" field will be ignored. The bits for" \
                                   u" but­tons, time stamp, and the serial number" \
                                   u" will also be ig­nored. In the case of" \
                                   u" overlapping contexts, movement events" \
                                   u" for data" \
                                   u" items not selected in this field may be" \
                                   u" processed by underlying con­texts."

CONTEXT_FIELD_DOCSTR['lcBtnDnMask']=u"Specifies the buttons for which button " \
                                    u"press events will be proc­essed" \
                                    u" in the context. In the case of " \
                                    u"overlapping contexts, button press events" \
                                    u" for buttons that are not selected in " \
                                    u"this field may be processed by " \
                                    u"underlying contexts."

CONTEXT_FIELD_DOCSTR['lcBtnUpMask']=u"Specifies the buttons for which button" \
                                    u" release events will be processed in the context. " \
                                    u"In the case of overlapping contexts," \
                                    u" button release events for buttons that" \
                                    u" are not selected" \
                                    u"in this field may be processed by " \
                                    u"underlying contexts." \
                                    u"If both press and re­lease events" \
                                    u" are selected for a button " \
                                    u"(see the lcBtnDnMask field above)," \
                                    u" then the interface will cause the " \
                                    u"context to implic­itly capture all tablet events" \
                                    u" while the button is down. In this " \
                                    u"case, events occurring outside the " \
                                    u"context will be" \
                                    u" clipped to the context and processed " \
                                    u"as if they had occurred in the context. " \
                                    u"When the but­ton is released, the " \
                                    u"context will receive the button release event," \
                                    u" and then event processing will return to normal."

CONTEXT_FIELD_DOCSTR['lcInOrgX']=u"Each specifies the origin of the context's" \
                                 u" input area in the tablet's native " \
                                 u"coordinates, along the x, y, and z axes," \
                                 u" respectively. Each will be clipped to the" \
                                 u" tablet native coordinate space when the" \
                                 u" context is opened or modified."
CONTEXT_FIELD_DOCSTR['lcInOrgY']=CONTEXT_FIELD_DOCSTR['lcInOrgX']
CONTEXT_FIELD_DOCSTR['lcInOrgZ']=CONTEXT_FIELD_DOCSTR['lcInOrgX']

CONTEXT_FIELD_DOCSTR['lcInExtX']=u"Each specifies the extent of the context's" \
                                 u" input area in the tablet's native" \
                                 u" coordinates, along the x, y, and z axes," \
                                 u" respectively. Each will be clipped to" \
                                 u" the tablet native coordinate space when" \
                                 u" the context is opened or modified."
CONTEXT_FIELD_DOCSTR['lcInExtY']=CONTEXT_FIELD_DOCSTR['lcInExtX']
CONTEXT_FIELD_DOCSTR['lcInExtZ']=CONTEXT_FIELD_DOCSTR['lcInExtX']

CONTEXT_FIELD_DOCSTR['lcOutOrgX']=u"Each specifies the origin of the context's" \
                                  u" output area in context output " \
                                  u"coordinates, along the x, y, and z axes," \
                                  u" respectively. Each is used in coordinate" \
                                  u" scaling for absolute mode only."
CONTEXT_FIELD_DOCSTR['lcOutOrgY']=CONTEXT_FIELD_DOCSTR['lcOutOrgX']
CONTEXT_FIELD_DOCSTR['lcOutOrgZ']=CONTEXT_FIELD_DOCSTR['lcOutOrgX']

CONTEXT_FIELD_DOCSTR['lcOutExtX']=u"Each specifies the extent of the context's" \
                                  u" output area in context output " \
                                  u"coordinates, along the x, y, and z" \
                                  u" axes, respectively. Each is used in" \
                                  u" coordinate scaling for absolute mode only."
CONTEXT_FIELD_DOCSTR['lcOutExtY']=CONTEXT_FIELD_DOCSTR['lcOutExtX']
CONTEXT_FIELD_DOCSTR['lcOutExtZ']=CONTEXT_FIELD_DOCSTR['lcOutExtX']

CONTEXT_FIELD_DOCSTR['lcSensX']=u"Each specifies the relative-mode " \
                                u"sensitivity factor for the " \
                                u"x, y, and z axes, respectively."
CONTEXT_FIELD_DOCSTR['lcSensY']=CONTEXT_FIELD_DOCSTR['lcSensX']
CONTEXT_FIELD_DOCSTR['lcSensZ']=CONTEXT_FIELD_DOCSTR['lcSensX']

CONTEXT_FIELD_DOCSTR['lcSysMode']=u"Specifies the system cursor tracking mode." \
                                  u" Zero specifies absolute; non-zero" \
                                  u" means relative."

CONTEXT_FIELD_DOCSTR['lcSysOrgX']=u"Together specify the origin of the screen" \
                                  u" mapping area for system cursor tracking," \
                                  u" in screen coordinates."
CONTEXT_FIELD_DOCSTR['lcSysOrgY']=CONTEXT_FIELD_DOCSTR['lcSysOrgX']

CONTEXT_FIELD_DOCSTR['lcSysExtX']=u"Together specify the extent of the screen" \
                                  u" mapping area for system cursor tracking," \
                                  u" in screen coordinates."
CONTEXT_FIELD_DOCSTR['lcSysExtY']=CONTEXT_FIELD_DOCSTR['lcSysExtX']

CONTEXT_FIELD_DOCSTR['lcSysSensX']=u"Each specifies the system-cursor" \
                                   u" relative-mode sensitivity factor" \
                                   u" for the x and y axes, respectively."
CONTEXT_FIELD_DOCSTR['lcSysSensY']=CONTEXT_FIELD_DOCSTR['lcSysSensX']
