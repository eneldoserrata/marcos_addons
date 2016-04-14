# -*- coding: utf-8 -*-

from openerp import models, fields, api
import calendar

class DgiiIt(models.Model):
    _name = 'dgii.report.it1'

    base_dict = {
            "II1_ids": True,
            "IIA2_ids": True,
            "IIA3_ids": True,
            "IIA4_ids": True,
            "IIA5_ids": True,
            "IIB6_ids": True,
            "IIB7_ids": True,
            "IIB8_ids": True,
            "IIB9_ids": True,
            "IIB10_ids": True,
            "IIB11_ids": True,
            "III12_ids": False,
            "III13_ids": False,
            "III14_ids": False,
            "III15_ids": False,
            "III16_ids": False,
            "III17_ids": False,
            "III18_ids": False,
            "III19_ids": False,
            "III20_ids": False,
            "III21_ids": False,
            "III22_ids": False,
            "III23_ids": False,
            "III24_ids": False,
            "III25_ids": False,
            "III26_ids": False,
            "III27_ids": False,
            "III28_ids": False,
            "III29_ids": False,
            "III30_ids": False,
            "III31_ids": False,
            "III32_ids": False,
            "III33_ids": False,
            "III34_ids": False,
            "A40_ids": False,
            "A41_ids": False,
            "A42_ids": False,
            "A43_ids": False,
            "A44_ids": False,
            "A45_ids": False,
            "A46_ids": False,
            "A47_ids": False,
            "A48_ids": False,
            "A49_ids": False,
            "A50_ids": False,
            "A51_ids": False,
            "A52_ids": False,
            "A53_ids": False,
            "A54_ids": False,
            "A55_ids": False,
            "A56_ids": False,
            "A57_ids": False,
            "A58_ids": False,
            "A59_ids": False,
            "A60_ids": False,
            "A61_ids": False,
            "A62_ids": False,
            "A63_ids": False
    }






    company_id = fields.Many2one("res.company", default=lambda s: s.env.user.company_id.id, string=u"Compañia")
    II1_ids = fields.Many2many("account.tax", relation='account_tax_ii1', column1="tax_id", column2="ii1_id", string=u"TOTAL DE OPERACIONES DEL PERÍODO")
    IIA2_ids = fields.Many2many("account.tax", relation='account_tax_iia2', column1="tax_id", column2="iia2_id", string=u"INGRESOS,POR EXPORTACIONES DE BIENES O SERVICIOS EXENTOS")
    IIA3_ids = fields.Many2many("account.tax", relation='account_tax_iia3', column1="tax_id", column2="iia3_id", string=u"INGRESOS,POR VENTAS LOCALES DE BIENES O SERVICIOS EXENTOS")
    IIA4_ids = fields.Many2many("account.tax", relation='account_tax_iia4', column1="tax_id", column2="iia4_id", string=u"INGRESOS POR VENTAS LOCALES DE BIENES O SERVICIOS,A ENTIDADES DEL ESTADO EXENTOS")
    IIA5_ids = fields.Many2many("account.tax", relation='account_tax_iia5', column1="tax_id", column2="iia5_id", string=u"TOTAL,INGRESOS POR OPERACIONES NO GRAVADAS (Sumar casillas,2+3+4)")
    IIB6_ids = fields.Many2many("account.tax", relation='account_tax_iib6', column1="tax_id", column2="iib6_id", string=u"TOTAL INGRESOS POR OPERACIONES GRAVADAS (Restar,casillas 1-5)")
    IIB7_ids = fields.Many2many("account.tax", relation='account_tax_iib7', column1="tax_id", column2="iib7_id", string=u"OPERACIONES GRAVADAS AL 18%")
    IIB8_ids = fields.Many2many("account.tax", relation='account_tax_iib8', column1="tax_id", column2="iib8_id", string=u"OPERACIONES GRAVADAS AL 16%")
    IIB9_ids = fields.Many2many("account.tax", relation='account_tax_iib9', column1="tax_id", column2="iib9_id", string=u"OPERACIONES GRAVADAS AL 1% (Ley No. 542-14)")
    IIB10_ids = fields.Many2many("account.tax", relation='account_tax_iib10', column1="tax_id", column2="iib10_id", string=u"OPERACIONES GRAVADAS AL 18% VENTAS LOCALES DE,BIENES O SERVICIOS A ENTIDADES DEL ESTADO")
    IIB11_ids = fields.Many2many("account.tax", relation='account_tax_iib11', column1="tax_id", column2="iib11_id", string=u"OPERACIONES GRAVADAS AL 16% VENTAS LOCALES DE BIENES O SERVICIOS A ENTIDADES DEL ESTADO")
    III12_ids = fields.Many2many("account.tax", relation='account_tax_iii12', column1="tax_id", column2="iii12_id", string=u"ITBIS COBRADO (18% de la casilla 7)")
    III13_ids = fields.Many2many("account.tax", relation='account_tax_iii13', column1="tax_id", column2="iii13_id", string=u"ITBIS COBRADO (16% de la casilla 8)")
    III14_ids = fields.Many2many("account.tax", relation='account_tax_iii14', column1="tax_id", column2="iii14_id", string=u"ITBIS COBRADO (1% de la casilla 9) (Ley No. 542-14)")
    III15_ids = fields.Many2many("account.tax", relation='account_tax_iii15', column1="tax_id", column2="iii15_id", string=u"ITBIS FACTURADO POR VENTAS LOCALES DE BIENES O,SERVICIOS A ENTIDADES DEL ESTADO (18% de la casilla 10)")
    III16_ids = fields.Many2many("account.tax", relation='account_tax_iii16', column1="tax_id", column2="iii16_id", string=u"ITBIS FACTURADO POR VENTAS LOCALES DE BIENES O,SERVICIOS A ENTIDADES DEL ESTADO (16% de la casilla 11)")
    III17_ids = fields.Many2many("account.tax", relation='account_tax_iii17', column1="tax_id", column2="iii17_id", string=u"TOTAL ITBIS FACTURADO POR VENTAS LOCALES DE BIENES,O SERVICIOS A ENTIDADES DEL ESTADO (Sumar casillas 15+16)")
    III18_ids = fields.Many2many("account.tax", relation='account_tax_iii18', column1="tax_id", column2="iii18_id", string=u"TOTAL ITBIS COBRADO (Sumar casillas,12+13+14+15+16)")
    III19_ids = fields.Many2many("account.tax", relation='account_tax_iii19', column1="tax_id", column2="iii19_id", string=u"ITBIS PAGADO EN COMPRAS LOCALES (Proviene del Formato de Envío,de Datos 606)")
    III20_ids = fields.Many2many("account.tax", relation='account_tax_iii20', column1="tax_id", column2="iii20_id", string=u"ITBIS PAGADO POR SERVICIOS DEDUCIBLES (Proviene del Formato de,Envío de Datos 606)")
    III21_ids = fields.Many2many("account.tax", relation='account_tax_iii21', column1="tax_id", column2="iii21_id", string=u"ITBIS PAGADO EN IMPORTACIONES")
    III22_ids = fields.Many2many("account.tax", relation='account_tax_iii22', column1="tax_id", column2="iii22_id", string=u"TOTAL ITBIS PAGADO (Sumar casillas 19+20+21)")
    III23_ids = fields.Many2many("account.tax", relation='account_tax_iii23', column1="tax_id", column2="iii23_id", string=u"IMPUESTO A PAGAR (Si el valor de las,casillas 18-22 es Positivo)")
    III24_ids = fields.Many2many("account.tax", relation='account_tax_iii24', column1="tax_id", column2="iii24_id", string=u"SALDO A FAVOR (Si el valor de las casillas,18-22 es Negativo)")
    III25_ids = fields.Many2many("account.tax", relation='account_tax_iii25', column1="tax_id", column2="iii25_id", string=u"SALDOS COMPENSABLES AUTORIZADOS (Otros Impuestos) Y/O REEMBOLSOS")
    III26_ids = fields.Many2many("account.tax", relation='account_tax_iii26', column1="tax_id", column2="iii26_id", string=u"SALDO A FAVOR ANTERIOR")
    III27_ids = fields.Many2many("account.tax", relation='account_tax_iii27', column1="tax_id", column2="iii27_id", string=u"PAGOS COMPUTABLES POR RETENCIONES (Norma No. 08-04)")
    III28_ids = fields.Many2many("account.tax", relation='account_tax_iii28', column1="tax_id", column2="iii28_id", string=u"PAGOS COMPUTABLES POR OTRAS RETENCIONES (Norma No. 02-05)")
    III29_ids = fields.Many2many("account.tax", relation='account_tax_iii29', column1="tax_id", column2="iii29_id", string=u"OTROS,PAGOS COMPUTABLES A CUENTA")
    III30_ids = fields.Many2many("account.tax", relation='account_tax_iii30', column1="tax_id", column2="iii30_id", string=u"CREDITO POR RETENCIÓN REALIZADA POR ENTIDADES DEL ESTADO")
    III31_ids = fields.Many2many("account.tax", relation='account_tax_iii31', column1="tax_id", column2="iii31_id", string=u"COMPENSACIONES Y/O REEMBOLSOS AUTORIZADOS")
    III32_ids = fields.Many2many("account.tax", relation='account_tax_iii32', column1="tax_id", column2="iii32_id", string=u"ITBIS DIFERIDO POR VENTAS A ENTIDADES DEL ESTADO")
    III33_ids = fields.Many2many("account.tax", relation='account_tax_iii33', column1="tax_id", column2="iii33_id", string=u"DIFERENCIA A PAGAR (Si el valor de las,casillas 23-25-26-27-28-29-30+31-32 es Positivo)")
    III34_ids = fields.Many2many("account.tax", relation='account_tax_iii34', column1="tax_id", column2="iii34_id", string=u"NUEVO SALDO A FAVOR (Si el valor de las,casillas,(23-25-26-27-28-29-30+31-32,es Negativo) ó (24+25+26+27+28+29+30+31+32))")
    A40_ids = fields.Many2many("account.tax", relation='account_tax_a40', column1="tax_id", column2="a40_id", string=u"SERVICIOS SUJETOS A RETENCIÓN PERSONAS,FÍSICAS")
    A41_ids = fields.Many2many("account.tax", relation='account_tax_a41', column1="tax_id", column2="a41_id", string=u"SERVICIOS SUJETOS A RETENCIÓN,ENTIDADES NO LUCRATIVAS")
    A42_ids = fields.Many2many("account.tax", relation='account_tax_a42', column1="tax_id", column2="a42_id", string=u"TOTAL SERVICIOS SUJETOS A RETENCIÓN A PERSONAS,FÍSICAS Y ENTIDADES NO LUCRATIVAS")
    A43_ids = fields.Many2many("account.tax", relation='account_tax_a43', column1="tax_id", column2="a43_id", string=u"SERVICIOS SUJETOS A RETENCIÓN SOCIEDADES")
    A44_ids = fields.Many2many("account.tax", relation='account_tax_a44', column1="tax_id", column2="a44_id", string=u"SERVICIOS SUJETOS A RETENCIÓN SOCIEDADES (Norma No. 02-05 y 07-07)")
    A45_ids = fields.Many2many("account.tax", relation='account_tax_a45', column1="tax_id", column2="a45_id", string=u"BIENES O SERVICIOS SUJETOS A RETENCIÓN A,CONTRIBUYENTES ACOGIDOS AL PST (Operaciones Gravadas al,18%)")
    A46_ids = fields.Many2many("account.tax", relation='account_tax_a46', column1="tax_id", column2="a46_id", string=u"BIENES O SERVICIOS SUJETOS A RETENCIÓN A,CONTRIBUYENTES ACOGIDOS AL PST (Operaciones Gravadas al,16%)")
    A47_ids = fields.Many2many("account.tax", relation='account_tax_a47', column1="tax_id", column2="a47_id", string=u"TOTAL BIENES O SERVICIOS SUJETOS A RETENCIÓN A,CONTRIBUYENTES ACOGIDOS AL PST")
    A48_ids = fields.Many2many("account.tax", relation='account_tax_a48', column1="tax_id", column2="a48_id", string=u"BIENES SUJETOS A RETENCIÓN PROVEEDORES INFORMALES (Operaciones Gravadas al 18%) (Norma No. 08-10)")
    A49_ids = fields.Many2many("account.tax", relation='account_tax_a49', column1="tax_id", column2="a49_id", string=u"BIENES SUJETOS A RETENCIÓN PROVEEDORES INFORMALES (Operaciones Gravadas al 16%) (Norma No. 08-10)")
    A50_ids = fields.Many2many("account.tax", relation='account_tax_a50', column1="tax_id", column2="a50_id", string=u"TOTAL BIENES SUJETOS A RETENCIÓN PROVEEDORES,INFORMALES (Norma No. 08-10)")
    A51_ids = fields.Many2many("account.tax", relation='account_tax_a51', column1="tax_id", column2="a51_id", string=u"ITBIS POR SERVICIOS SUJETOS A RETENCIÓN PERSONAS,FÍSICAS Y ENTIDADES NO LUCRATIVAS (18% de la casilla 42)")
    A52_ids = fields.Many2many("account.tax", relation='account_tax_a52', column1="tax_id", column2="a52_id", string=u"ITBIS POR SERVICIOS SUJETOS A RETENCIÓN SOCIEDADES (18% de la casilla 43)")
    A53_ids = fields.Many2many("account.tax", relation='account_tax_a53', column1="tax_id", column2="a53_id", string=u"ITBIS POR SERVICIOS SUJETOS A RETENCIÓN SOCIEDADES (18% de la casilla 44 por 0.30) (Norma No. 02-05 y 07-07)")
    A54_ids = fields.Many2many("account.tax", relation='account_tax_a54', column1="tax_id", column2="a54_id", string=u"ITBIS RETENIDO A CONTRIBUYENTES ACOGIDOS AL PST (18% de la casilla 45)	")
    A55_ids = fields.Many2many("account.tax", relation='account_tax_a55', column1="tax_id", column2="a55_id", string=u"ITBIS RETENIDO A CONTRIBUYENTES ACOGIDOS AL PST (16%,de la casilla 46)")
    A56_ids = fields.Many2many("account.tax", relation='account_tax_a56', column1="tax_id", column2="a56_id", string=u"TOTAL ITBIS RETENIDO A CONTRIBUYENTES ACOGIDOS AL,PST")
    A57_ids = fields.Many2many("account.tax", relation='account_tax_a57', column1="tax_id", column2="a57_id", string=u"ITBIS POR BIENES SUJETOS A RETENCIÓN PROVEEDORES,INFORMALES (18% de la casilla 48 por 0.75) (Norma No. 08-10)")
    A58_ids = fields.Many2many("account.tax", relation='account_tax_a58', column1="tax_id", column2="a58_id", string=u"ITBIS POR BIENES SUJETOS A RETENCIÓN PROVEEDORES,INFORMALES (16% de la casilla 49 por 0.75) (Norma No. 08-10)")
    A59_ids = fields.Many2many("account.tax", relation='account_tax_a59', column1="tax_id", column2="a59_id", string=u"TOTAL POR BIENES SUJETOS A RETENCIÓN PROVEEDORES,INFORMALES")
    A60_ids = fields.Many2many("account.tax", relation='account_tax_a60', column1="tax_id", column2="a60_id", string=u"IMPUESTO A PAGAR (Sumar,casillas 51+52+53+56+59)")
    A61_ids = fields.Many2many("account.tax", relation='account_tax_a61', column1="tax_id", column2="a61_id", string=u"PAGOS COMPUTABLES A CUENTA")
    A62_ids = fields.Many2many("account.tax", relation='account_tax_a62', column1="tax_id", column2="a62_id", string=u"DIFERENCIA A PAGAR (Si el,valor de las casillas 60-61 es Positivo)")
    A63_ids = fields.Many2many("account.tax", relation='account_tax_a63', column1="tax_id", column2="a63_id", string=u"NUEVO SALDO A FAVOR (Si el,valor de las casillas 60-61 es Negativo)")


    def get_invoice_domain(self, month, year):
        max_day = str(calendar.monthrange(int(year), int(month))[1])
        from_date = "{}-{}-01".format(year, month)
        to_date = "{}-{}-{}".format(year, month, max_day)
        return {'from_date': from_date, 'to_date': to_date, "tax_ids": False}

    def make_query(self, params, key):
        query = """
        SELECT
         "public"."account_invoice_tax"."amount",
         "public"."account_invoice"."amount_untaxed_signed"
        FROM     "account_invoice_tax"
        INNER JOIN "account_invoice"  ON "account_invoice_tax"."invoice_id" = "account_invoice"."id"
        where "public"."account_invoice"."date_invoice" BETWEEN '{}' and '{}'
        and "public"."account_invoice"."state" in ('paid','open')
        and "public"."account_invoice_tax"."tax_id" in {}
        """.format(params["from_date"], params["to_date"], params["tax_ids"])
        self._cr.execute(query)
        res = self._cr.fetchall()
        tax = 0
        base = 0
        for rec in res:
            if rec[1] < 0:
                tax -= rec[0]
            else:
                tax += rec[0]

            base += rec[1]
        return {"tax": tax, "base": base, "base_amount": self.base_dict[key]}


    @api.model
    def get_report(self, month, year):
        res = {}

        try:
            query_parameters = self.get_invoice_domain(month, year)
        except:
            return False

        config = self.search([('company_id','=',self.env.user.company_id.id)])


        keys = [key for key in self._fields.keys() if key[0] in ('A','I')]
        for key in keys:
            tax_ids = tuple([rec.id for rec in config[key]])
            if tax_ids:
                if len(tax_ids) == 1:
                    tax_ids = "({})".format(tax_ids[0])
                query_parameters.update({"tax_ids": tax_ids})
                res[key] = self.make_query(query_parameters, key)
            else:
                res[key] = {"tax": 0.00, "base": 0.00, "base_amount": self.base_dict[key]}

        return res


