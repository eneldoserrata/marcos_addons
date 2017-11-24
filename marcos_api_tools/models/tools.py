# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################

import sys
import csv

csv.field_size_limit(sys.maxsize)

import urllib2

__author__ = 'eneldoserrata'

excepcionesCedulas = ['00208430205', '00101118022', '00167311001', '00102025201', '02755972001', '01038813907',
                      '01810035037', '00161884001', '00102630192', '00000021249', '00144435001', '00100350928',
                      '00100523399', '00109402756', '00101659661', '00539342005', '00104662561', '08016809001',
                      '05500012039', '00104486903', '00103754365', '01200014133', '10983439110', '08498619001',
                      '00104862525', '00100729795', '00644236001', '01650257001', '00170009162', '00651322001',
                      '00297018001', '00100288929', '00190002567', '01094560111', '01300020331', '00109785951',
                      '00110047715', '05400067703', '00100061945', '00100622461', '02831146001', '10462157001',
                      '00100728113', '00108497822', '00481106001', '00100181057', '10491297001', '00300244009',
                      '00170115579', '02038569001', '00100238382', '03852380001', '00100322649', '00107045499',
                      '00100384523', '00130610001', '06486186001', '00101621981', '00201023001', '00520207699',
                      '00300636564', '00000140874', '05700071202', '03100673050', '00189405093', '00105328185',
                      '10061805811', '00117582001', '00103443802', '00100756082', '00100239662', '04700027064',
                      '04700061076', '05500023407', '05500017761', '05400049237', '05400057300', '05600038964',
                      '05400021759', '00100415853', '05500032681', '05500024190', '06400011981', '05500024135',
                      '06400007916', '05500014375', '05500008806', '05500021118', '05600051191', '00848583056',
                      '00741721056', '04801245892', '04700004024', '00163709018', '05600267737', '00207327056',
                      '00731054054', '00524571001', '00574599001', '00971815056', '06800008448', '04900011690',
                      '03111670001', '00134588056', '04800019561', '05400040523', '05400048248', '05600038251',
                      '00222017001', '06100011935', '06100007818', '00129737056', '00540077717', '00475916056',
                      '00720758056', '02300062066', '02700029905', '02600094954', '11700000658', '03100109611',
                      '04400002002', '03400157849', '03900069856', '00100524531', '00686904003', '00196714003',
                      '00435518003', '00189213001', '06100009131', '02300085158', '02300047220', '00100593378',
                      '00100083860', '00648496171', '00481595003', '00599408003', '00493593003', '00162906003',
                      '00208832003', '00166533003', '00181880003', '00241997013', '00299724003', '00174729003',
                      '01000005580', '00400012957', '00100709215', '08900001310', '05400053627', '05400055770',
                      '08800003986', '02300031758', '01154421047', '00300013835', '00300011700', '01300001142',
                      '00147485003', '00305535206', '05400054156', '06100016486', '00100172940', '04800046910',
                      '00101527366', '00270764013', '00184129003', '05400033166', '05400049834', '05400062459',
                      '09700003030', '05300013029', '05400037495', '05400028496', '05400059956', '05400072273',
                      '02300052220', '00356533003', '00163540003', '00376023023', '00362684023', '00633126023',
                      '00278005023', '00235482001', '00142864013', '00131257003', '00236245013', '00757398001',
                      '00146965001', '00516077003', '00425759001', '00857630012', '06843739551', '02300023225',
                      '00298109001', '00274652001', '00300017875', '00300025568', '01300005424', '00103266558',
                      '00174940001', '00289931003', '00291549003', '02800021761', '02800029588', '01000268998',
                      '02600036132', '00200040516', '01100014261', '02800000129', '01200033420', '02800025877',
                      '00300020806', '00200021994', '00200063601', '07600000691', '09300006239', '00200028716',
                      '04900028443', '00163549012', '01200008613', '01200011252', '01100620962', '00100255349',
                      '00108796883', '03102828522', '00000719400', '00004110056', '00000065377', '00000292212',
                      '00000078587', '00000126295', '00000111941', '12019831001', '00171404771', '03000411295',
                      '00000564933', '00000035692', '00143072001', '03102936385', '00000155482', '00000236621',
                      '00400001552', '04941042001', '00300169535', '00102577448', '03600127038', '00100174666',
                      '00100378440', '00104785104', '00101961125', '05600063115', '00110071113', '00100000169',
                      '04902549001', '00155144906', '06337850001', '02300054193', '00100016495', '00101821735',
                      '00544657001', '03807240010', '08952698001', '00345425001', '06100013662', '08900005064',
                      '05400058964', '05400022042', '05400055485', '05400016031', '05400034790', '05400038776',
                      '05400076481', '05400060743', '05400047674', '00246160013', '00116256005', '00261011013',
                      '01600026316', '00103983004', '05600037761', '00291431001', '00100530588', '01600009531',
                      '05500022399', '05500003079', '05500006796', '05500027749', '06400014372', '00352861001',
                      '00100053841', '00218507031', '02300037618', '04600198229', '00000058035', '04700074827',
                      '04700070460', '04700020933', '07800000968', '00300019575', '00100126468', '00300001538',
                      '03100984652', '00388338093', '58005174058', '00100074627', '00100531007', '00000669773',
                      '00100430989', '00000144491', '00000404655', '00000031417', '00000302347', '00000195576',
                      '00000129963', '00000045342', '00000547495', '00409169001', '00166457056', '00001965804',
                      '03102399233', '03100332296', '03100442457', '03170483480', '03100620176', '00572030001',
                      '00300040413', '05600166034', '03100789636', '03101456639', '00107075090', '00104966313',
                      '03100001162', '03103202719', '03100231390', '03101713684', '03100083297', '03101977306',
                      '03100195659', '03102342076', '03100232921', '03102678700', '03100486248', '01133025660',
                      '07401860112', '01103552230', '00300015531', '00160405001', '05400065376', '08900004344',
                      '05400052300', '05400057684', '05700004693', '03100277078', '00108940225', '03100156525',
                      '03107049671', '03101162278', '03100771674', '09400022178', '03131503831', '04200012900',
                      '04700211635', '03101014877', '03100018730', '03100831768', '03101105802', '03101577963',
                      '01200027863', '01200038298', '03101409196', '03100304632', '09200533048', '03102805428',
                      '03100034839', '03108309308', '03101477254', '00077584000', '00101234090', '00100336027',
                      '00100384268', '00100664086', '00103766231', '03103317617', '03100398552', '03100668294',
                      '05400878578', '05900105969', '05300013204', '00500335596', '00561269169', '08000213172',
                      '08400068380', '04700728184', '00010130085', '05300123494', '00010628559', '21000000000']

excepcionesRNC = ['501378067', '501656006', '501620371', '501651319', '501651845', '501651926', '501670785',
                  '501676936', '501658167', '505038691', '501680158', '501341601', '501651823', '504680029',
                  '504681442', '504654542']


def mod11(value):
    num = list(map(int, value))  # convierte string en lista de string
    suma = 0
    pesoRNC = [7, 9, 8, 6, 5, 4, 3, 2]  # Mod11 pero el RNC utiliza su propio sistema de peso.
    for index in range(len(pesoRNC)):
        suma += (pesoRNC[index] * num[index])

    resto = suma % 11
    if resto == 0:
        digito = 2
    elif resto == 1:
        digito = 1
    else:
        digito = 11 - resto
    return digito == int(value[-1])


def mod10(number):
    num = map(int, str(number))
    return sum(num[::-2] + [sum(divmod(d * 2, 10)) for d in num[-2::-2]]) % 10 == 0


def is_identification(value):
    """
    Valida las identificaciones fiscales de la República Dominicana
    Cédula de identidad personal y Registro nacional del contribuyente
    :param value: recibe una cédula o RNC
    """
    if not value:
        return False
    if len(value) > 0:
        value = value.strip()

    if (len(value) == 9 or len(value) == 11) and value.isdigit():  # Valida logitud y Valida que solo sean numeros
        if len(value) == 11:  # si tiene 11 digitos es una cedula
            if value in excepcionesCedulas:  # valida en el listado
                return True
            else:  # valida el algoritmo de (LUHN)
                return mod10(value)
        else:
            if value in excepcionesRNC:
                return True
            else:
                return mod11(value)
    else:
        return False


def is_ncf(value, type):
    u"""
    Valida estructura del Número de Comprobante Ficasl (NCF)
    para República Dominicana.

    Caracter 1: Serie
        Valores Permitidos: A o P
    Caracter 2-3: División de Negocios
        Valores Permitidos: 1 al 99
    Caracter 4-6: Punto de Emisión
        Valores Permitidos: 1 al 999
    Caracter 7-9: Area de Impresión
        Valores Permitidos: 1 al 999
    Caracter 10-11: Tipo de Comprobante
        Valores Permitidos: 01, 02, 03, 04, 11, 12, 13, 14, 15
    Caracter 12-19: Secuendial
        Valores Permitidos: 1 al 99,999,999 (sin comas)

    Tamaño: 19 Caracteres

    :param value: string con NCF

    :returns: True cuando tiene exito, False cuando falla.
    """
    if not value:
        return False

    value = value.strip()
    if len(value) == 19:
        try:
            if type in ("in_refund", "out_refund") and value[0] in ('A', 'P') and int(value[1:3]) and int(
                    value[3:6]) and int(value[6:9]) and value[9:11] == '04' and int(value[11:20]):
                return True
            elif type == "in_invoice" and value[0] in ('A', 'P') and int(value[1:3]) and int(value[3:6]) and int(
                    value[6:9]) and value[9:11] in ('01', '14', '15', '11', '13') and int(value[11:20]):
                return True
            elif type == "out_invoice" and value[0] in ('A', 'P') and int(value[1:3]) and int(value[3:6]) and int(
                    value[6:9]) and value[9:11] in ('01', '02', '14', '15', '11', '13') and int(value[11:20]):
                return True
        except:
            pass
    return False


def _internet_on(api_marcos):
    """TODO: fix this check"""
    return True
    try:
        response = urllib2.urlopen(api_marcos, timeout=1)
        return True
    except urllib2.URLError as err:
        pass
    return False
