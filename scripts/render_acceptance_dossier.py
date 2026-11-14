"""Generate a concise, unsigned scientific UAT pack; reference is the editable Markdown docs."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'RADAR_CORUNA_v31_Dossier_Aceptacion.pdf'
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DVS', REG))
pdfmetrics.registerFont(TTFont('DVS-Bold', BOLD))
NAVY=colors.HexColor('#203854')
INK=colors.HexColor('#2d3d52')
MUTED=colors.HexColor('#617084')
BLUE=colors.HexColor('#356d9f')
HAIR=colors.HexColor('#d7e0e9')
BG=colors.HexColor('#f5f8fb')
styles={
 'super':ParagraphStyle('super',fontName='DVS-Bold',fontSize=8.0,leading=12,textColor=BLUE,spaceAfter=13),
 'title':ParagraphStyle('title',fontName='DVS-Bold',fontSize=24,leading=31,textColor=NAVY,spaceAfter=8),
 'subtitle':ParagraphStyle('subtitle',fontName='DVS',fontSize=11,leading=16,textColor=MUTED,spaceAfter=20),
 'h':ParagraphStyle('h',fontName='DVS-Bold',fontSize=12.2,leading=17,textColor=NAVY,spaceBefore=14,spaceAfter=8),
 'body':ParagraphStyle('body',fontName='DVS',fontSize=9,leading=15,textColor=INK,spaceAfter=8),
 's':ParagraphStyle('small',fontName='DVS',fontSize=7.5,leading=11.8,textColor=INK),
 'sb':ParagraphStyle('smallbold',fontName='DVS-Bold',fontSize=7.7,leading=11.8,textColor=NAVY),
 'tiny':ParagraphStyle('tiny',fontName='DVS',fontSize=7,leading=11,textColor=MUTED),
}
def P(s,style='body'):return Paragraph(s,styles[style])
def tab(headers,rows,widths,fs=7,pad=7):
  data=[[P(x,'sb') for x in headers]]+[[P(str(x),'s') for x in row] for row in rows]
  t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.9,BLUE),('LINEBELOW',(0,1),(-1,-1),.42,HAIR),('BACKGROUND',(0,0),(-1,0),BG),('LEFTPADDING',(0,0),(-1,-1),pad),('RIGHTPADDING',(0,0),(-1,-1),pad),('TOPPADDING',(0,0),(-1,-1),6.3),('BOTTOMPADDING',(0,0),(-1,-1),6.3)]))
  return t

def frame(canvas,doc):
 canvas.saveState()
 w,h=A4
 canvas.setStrokeColor(HAIR);canvas.setLineWidth(.7)
 canvas.line(44,h-48,w-44,h-48)
 canvas.setFont('DVS-Bold',8);canvas.setFillColor(NAVY)
 canvas.drawString(44,h-36,'RADAR-CORUÑA')
 canvas.setFont('DVS',7);canvas.setFillColor(MUTED)
 canvas.drawRightString(w-44,h-36,'EVALUACIÓN CIENTÍFICA · V0.31')
 canvas.line(44,43,w-44,43)
 canvas.setFont('DVS',7)
 canvas.drawString(44,28,'USO EXCLUSIVO DE EVALUACIÓN · DATOS FICTICIOS')
 canvas.drawRightString(w-44,28,f'12.11.2026    ·    {doc.page}')
 canvas.restoreState()

story=[]
story += [Spacer(1,21),P('PAQUETE DE VALIDACIÓN / NEUMACT','super'),P('Aceptación científica<br/>y prueba guiada','title'),P('RADAR-CORUÑA · Estudio multicéntrico de control clínico de EPOC en Atención Primaria','subtitle')]
story += [P('Estado de la entrega','h'),P('<b>Preparación técnica para UAT completada.</b> La revisión científica por investigadores, la ratificación metodológica y el visto bueno institucional siguen pendientes. Este dossier no contiene firmas ni habilita datos reales.')]
story += [P('Qué se entrega','h'),tab(['Evidencia','Contenido'],[
 ('Control de elegibilidad','Preflight local de sólo lectura: edad, espirometría, estabilidad, consentimiento, exclusiones y visitas.'),
 ('Pruebas automatizadas','8 escenarios específicos de Fase 5: observación científica, permisos, trazabilidad y Excel.'),
 ('Prueba de investigadores','14 recorridos U01–U14 y acta de aceptación sin completar.'),
 ('Control de cambios','V0.30 preservada. V0.31 añade auditoría y documentos; sin cambios de cálculo RADAR ni criterios forzados.')
],[150,356])]
story += [P('Discordancias relevantes identificadas','h'),tab(['Criterio de protocolo','Hallazgo a resolver'],[
 ('Edad ≥40 años','No se bloquea automáticamente una inclusión con edad inferior.'),
 ('FEV1/FVC pos-BD &lt;0,70','La captura admite cocientes no obstructivos; falta evidencia estructurada de posbroncodilatación.'),
 ('Seguimiento AP previo','Falta evidencia fechada de consulta de control de EPOC en el año anterior.'),
 ('Consentimiento y exclusiones','Faltan reglas cerradas para algunos campos incompletos antes de dar por válida inclusión.'),
],[150,356])]
story += [Spacer(1,9),P('El inicio previsto en enero de 2027 está condicionado al dictamen favorable del comité de ética y a las autorizaciones pertinentes.','tiny')]
story += [PageBreak(),P('01   /   RECORRIDO','super'),P('Prueba guiada por investigadores','title'),P('Marcar P (pasa), I (incidencia) o NA (no ejecutado), y documentar todo fallo crítico.','body')]
uat=[
 ('U01','Admin y centros','Identificar los centros ficticios y el rol general.'),
 ('U02','Investigador Costa','No acceder a registros de Interior, tampoco con URL directa.'),
 ('U03','Revisor','Lectura de la trayectoria; cualquier escritura rechazada.'),
 ('U04','Cribado e inclusión','Cuatro semanas, criterios, consentimiento y ausencia de supuestos.'),
 ('U05','Edad y ratio','38 años o FEV1/FVC 0,75: incidencia científica en preflight.'),
 ('U06','RADAR V0','Cuatro «No»: cero válido; CAT=0, mMRC=0.'),
 ('U07','V1 y V2','Fechas correctas y desviación temporal visible, sin corregirla.'),
 ('U08','IANUS/R107','Distinción entre verificación, recetas y causa de ausencia.'),
 ('U09','Episodios/contactos','Un episodio EPOC con Urgencias e ingreso vinculados.'),
 ('U10','Evento no EPOC','No suma como agudización por EPOC.'),
 ('U11','Corrección y auditoría','Motivo, versiones y datos antes/después.'),
 ('U12','Longitudinal y Excel','V0–V2, denominadores válidos y exportación coherente.'),
 ('U13','Móvil 390 px','Menú, campos y acciones proporcionadas, sin desbordamiento.'),
 ('U14','Cerrar sesión','Persistencia sólo de lo guardado; sin cruce entre sesiones.'),
]
story += [tab(['ID','Área','Criterio esperado','P / I / NA'],[(i,a,b,'□ / □ / □') for i,a,b in uat],[43,130,268,65],pad=5)]
story += [Spacer(1,13),P('Registrar por cada incidencia: escenario, perfil, dispositivo, pasos, resultado esperado/observado, severidad, responsable y retest.','tiny')]
story += [PageBreak(),P('02   /   CONCORDANCIA','super'),P('Decisiones para el IP','title'),P('Lo documentado, lo implementado y lo formalmente aprobado son estados distintos.','body')]
story += [tab(['Ref.','Tema','Situación a 12/11/2026'],[
 ('DC-01','Resultado primario','Protocolo fija prevalencia basal RADAR ≥4; D01 histórico del catálogo aún figura como pregunta.'),
 ('DC-02','Estabilidad','Cuatro semanas sin agudización: regla resuelta y comprobada.'),
 ('DC-03','Edad y cociente','Corregir/checkear edad ≥40 y FEV1/FVC pos-BD <0,70 antes de uso real.'),
 ('DC-04','Seguimiento/consentimiento','Acordar evidencia de consulta previa, fecha y verificación de consentimiento.'),
 ('DC-05','R055/R056','Dos significados separados, pero ventana IANUS exacta pendiente.'),
 ('DC-06','R074, R081, R082','Episodio distinto de sus contactos; comprobar con clínicos.'),
 ('DC-07','R049–R052, R065','Hitos longitudinales y vínculo de evaluador con profesional por ratificar.'),
 ('DC-08','R107','Homologación de estados de ausencia aún pendiente.'),
 ('DC-09','Ventanas V1/V2','Se señalan desviaciones; análisis fuera de ventana por definir.'),
 ('DC-10','Sedes y roles','Centros interesados no equivalen a centros activados ni autorizados.'),
 ('DC-11','Entorno real','Cuenta demo y SQLite local sólo para simulación: migración institucional pendiente.'),
 ('DC-12','Ética','Falta documento de dictamen favorable en el paquete; no comenzar reclutamiento.'),
],[56,128,322],pad=6)]
story += [Spacer(1,16),P('Prioridad de cierre','h'),P('Primero resolver los requisitos críticos de elegibilidad, protección de datos y autorización. Después cerrar la concordancia de variables, ejecutar UAT con profesionales y congelar una versión acordada del CRD y del diccionario.')]
story += [PageBreak(),P('03   /   RESOLUCIÓN','super'),P('Acta sin completar','title'),P('Esta hoja no constituye aprobación. Completar después de la revisión presencial o remota.','body')]
story += [P('Responsables y sesión','h'),tab(['Función','Confirmación / fecha'],[
 ('Investigador principal · Dr. Manuel Fernández Rivas','________________________________________'),
 ('Coordinación científica · Dr. Pedro Jorge Marcos Rodríguez','________________________________________'),
 ('Investigadores de centro','________________________________________'),
 ('Responsable técnico y relator de incidencias','________________________________________'),
],[255,251])]
story += [P('Resultados UAT','h'),P('Escenarios ejecutados: ______ / 14       Correctos: ______       Incidencias críticas: ______       Pendientes: ______')]
story += [P('Propuesta de resolución','h'),P('□ No aceptado      □ Repetir UAT tras correcciones      □ Aceptación condicionada sólo del diseño      □ Aprobación científica de versión definida')]
story += [P('Condiciones, decisiones y responsables','h')]
for _ in range(4):story.append(P('__________________________________________________________________________________________________','body'))
story += [P('Puertas institucionales independientes','h'),P('□ CEIm/CEIC y autorizaciones       □ Centros activados       □ Seguridad/RGPD       □ Cuentas reales y permisos       □ Documentos concordantes')]
story += [Spacer(1,18),P('Firma IP: _____________________________________     Coordinación: _____________________________________','body')]
story += [P('Fecha de resolución: _______________________        Versión autorizada (si procede): ________________________','body')]
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=66,bottomMargin=64,title='RADAR-CORUÑA | Dossier de aceptación científica v0.31',author='RADAR-CORUÑA · soporte metodológico',subject='Guía y acta UAT no firmadas')
doc.build(story,onFirstPage=frame,onLaterPages=frame)
print(OUT)
