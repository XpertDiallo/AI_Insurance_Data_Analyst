from __future__ import annotations

import io
import json
import os
import uuid
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from insurance_ai.agents.analysis_agent import AnalysisAgent
from insurance_ai.core.audit import AuditLogger
from insurance_ai.core.config import settings
from insurance_ai.core.models import ReportPayload, TransformationRecord
from insurance_ai.core.project_store import ProjectStore
from insurance_ai.reports.generator import ReportGenerator
from insurance_ai.services.auth import AuthService
from insurance_ai.services.charts import ChartService
from insurance_ai.services.cleaning import CleaningService
from insurance_ai.services.database import DatabaseService
from insurance_ai.services.dashboard import DashboardService
from insurance_ai.services.gemini_manager import GeminiModelManager
from insurance_ai.services.ingestion import IngestionService
from insurance_ai.services.insurance_kpi import InsuranceKPIService
from insurance_ai.services.profiling import ProfilingService
from insurance_ai.services.quality_rules import DataQualityRuleEngine

st.set_page_config(page_title=settings.app_name, page_icon="🛡️", layout="wide")

# -----------------------------------------------------------------------------
# Services
# -----------------------------------------------------------------------------
store = ProjectStore()
audit = AuditLogger()
ingestion = IngestionService()
profiler = ProfilingService()
cleaner = CleaningService()
kpi_service = InsuranceKPIService()
reporter = ReportGenerator()
dashboard_service = DashboardService()
quality_rules = DataQualityRuleEngine()
llm = GeminiModelManager()
analysis_agent = AnalysisAgent(llm=llm)


def init_state() -> None:
    defaults = {
        "user": {"username": "demo", "role": "admin", "display_name": "Demo"},
        "project_id": None,
        "project_name": "",
        "dataset_meta": None,
        "df": None,
        "stage": None,
        "analysis_results": [],
        "report_charts": [],
        "db_service": None,
        "raw_preview": None,
        "raw_preview_info": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def auth_gate() -> None:
    if not settings.auth_enabled:
        return
    if st.session_state.get("authenticated"):
        return
    st.title("🔐 Connexion")
    with st.form("login"):
        username = st.text_input("Utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
    if submitted:
        user = AuthService().authenticate(username, password)
        if user:
            st.session_state.user = user
            st.session_state.authenticated = True
            audit.log("login", user=username)
            st.rerun()
        st.error("Identifiants invalides.")
    st.stop()


def current_df() -> pd.DataFrame | None:
    value = st.session_state.get("df")
    return value if isinstance(value, pd.DataFrame) else None


def require_df() -> pd.DataFrame:
    df = current_df()
    if df is None:
        st.warning("Importez ou connectez d'abord un dataset.")
        st.stop()
    return df


def ensure_project(name: str | None = None) -> str:
    if st.session_state.project_id:
        return st.session_state.project_id
    pname = (name or st.session_state.project_name or "Nouveau projet").strip()
    pid = store.create_project(pname, owner=st.session_state.user["username"])
    st.session_state.project_id = pid
    st.session_state.project_name = pname
    audit.log("project_created", {"name": pname}, user=st.session_state.user["username"], project_id=pid)
    return pid


def visible_projects() -> list[dict]:
    projects = store.list_projects()
    role = st.session_state.user.get("role", "business")
    if role in {"admin", "auditor"}:
        return projects
    username = st.session_state.user.get("username")
    return [p for p in projects if p.get("owner") == username]


def save_version(df: pd.DataFrame, stage: str, source_type: str, source_name: str, parent_id: str | None = None):
    pid = ensure_project()
    meta = store.save_dataframe(
        pid, df, name=st.session_state.project_name or source_name, stage=stage,
        source_type=source_type, source_name=source_name, parent_id=parent_id,
    )
    st.session_state.dataset_meta = meta.to_dict()
    st.session_state.df = df
    st.session_state.stage = stage
    return meta


def log_transform(operation: str, before: pd.DataFrame, after: pd.DataFrame, column=None, parameters=None):
    pid = st.session_state.project_id
    meta = st.session_state.dataset_meta or {}
    if not pid or not meta:
        return
    rec = TransformationRecord(
        transformation_id=uuid.uuid4().hex[:12],
        dataset_id=meta.get("dataset_id", "unknown"),
        operation=operation,
        column=column,
        parameters=parameters or {},
        rows_before=len(before),
        rows_after=len(after),
        user=st.session_state.user["username"],
    )
    store.log_transformation(pid, rec)
    audit.log("transformation", rec.to_dict(), user=st.session_state.user["username"], project_id=pid)


def dataframe_download(df: pd.DataFrame, fmt: str) -> tuple[bytes, str, str]:
    fmt = fmt.lower()
    if fmt == "csv":
        return df.to_csv(index=False).encode("utf-8-sig"), "dataset.csv", "text/csv"
    if fmt == "xlsx":
        b = io.BytesIO()
        with pd.ExcelWriter(b, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Data")
        return b.getvalue(), "dataset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if fmt == "parquet":
        b = io.BytesIO(); df.to_parquet(b, index=False)
        return b.getvalue(), "dataset.parquet", "application/octet-stream"
    raise ValueError(fmt)


init_state()
auth_gate()

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
ROLE_PAGES = {
    "admin": ["Accueil", "Importer", "Qualité", "Nettoyage", "Analyse IA", "Assurance KPI", "Dashboard", "Base SQL", "Rapports", "Audit", "Paramètres"],
    "analyst": ["Accueil", "Importer", "Qualité", "Nettoyage", "Analyse IA", "Assurance KPI", "Dashboard", "Base SQL", "Rapports", "Audit"],
    "business": ["Accueil", "Importer", "Qualité", "Nettoyage", "Analyse IA", "Assurance KPI", "Dashboard", "Rapports"],
    "manager": ["Accueil", "Analyse IA", "Assurance KPI", "Dashboard", "Rapports"],
    "auditor": ["Accueil", "Qualité", "Audit"],
}

with st.sidebar:
    st.title("🛡️ AI Insurance Data Analyst V2")
    role = st.session_state.user.get("role", "business")
    page = st.radio("Navigation", ROLE_PAGES.get(role, ROLE_PAGES["business"]))
    st.divider()
    st.caption(f"Utilisateur : {st.session_state.user['display_name']} ({st.session_state.user['role']})")
    if st.session_state.project_id:
        st.caption(f"Projet : {st.session_state.project_name}")
    if st.session_state.stage:
        st.info(f"Dataset actif : {st.session_state.stage}")

# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------
if page == "Accueil":
    st.header("AI Insurance Data Analyst V2")
    st.write("Copilote professionnel pour connecter, profiler, nettoyer, analyser, visualiser et reporter les données d'assurance.")
    projects = visible_projects()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Projets visibles", len(projects))
    c2.metric("Gemini", "Configuré" if llm.enabled else "Mode déterministe")
    c3.metric("Dataset", "Oui" if current_df() is not None else "Non")
    c4.metric("Étape", st.session_state.stage or "—")
    st.markdown("**Processus recommandé :** Connect → Profile → Clean → Validate → Analyze → Visualize → Report → Export")
    if projects:
        st.subheader("Ouvrir un projet existant")
        labels = {f"{p.get('name')} — {p.get('project_id')}": p for p in projects}
        selected_label = st.selectbox("Projet", list(labels), key="open_project_label")
        selected = labels[selected_label]
        datasets = store.list_datasets(selected["project_id"])
        if datasets:
            def _priority(d):
                return {"CURATED":0,"STAGING":1,"RAW":2}.get(d.get("stage"),3)
            datasets = sorted(datasets, key=lambda d: (_priority(d), d.get("created_at", "")))
            dlabels = {f"{d.get('stage')} — {d.get('name')} — {d.get('dataset_id')}": d for d in datasets}
            dlabel = st.selectbox("Version du dataset", list(dlabels), key="open_dataset_label")
            selected_dataset = dlabels[dlabel]
            if st.button("Ouvrir le projet et la version", type="primary"):
                st.session_state.project_id = selected["project_id"]
                st.session_state.project_name = selected.get("name", "")
                st.session_state.dataset_meta = selected_dataset
                st.session_state.stage = selected_dataset.get("stage")
                st.session_state.df = store.load_dataframe(selected["project_id"], selected_dataset["dataset_id"])
                audit.log("project_opened", {"dataset_id": selected_dataset["dataset_id"]}, user=st.session_state.user["username"], project_id=selected["project_id"])
                st.success("Projet ouvert.")
                st.rerun()
        st.dataframe(pd.DataFrame(projects), use_container_width=True, hide_index=True)

elif page == "Importer":
    st.header("📥 Importer des données")
    st.session_state.project_name = st.text_input("Nom du projet", value=st.session_state.project_name or "Analyse portefeuille")
    uploaded = st.file_uploader("CSV/TXT, Excel ou JSON", type=["csv","txt","tsv","xlsx","xls","xlsm","json"])
    if uploaded:
        raw = uploaded.getvalue()
        if len(raw) > settings.max_upload_mb * 1024 * 1024:
            st.error(f"Fichier trop volumineux. Limite applicative : {settings.max_upload_mb} MB")
            st.stop()
        suffix = os.path.splitext(uploaded.name)[1].lower()
        kwargs = {}
        if suffix in ingestion.CSV_EXTENSIONS:
            detection = ingestion.detect_csv(raw)
            st.info(f"Détection : séparateur={repr(detection.delimiter)} | encodage={detection.encoding} | décimale={detection.decimal}")
            c1,c2,c3 = st.columns(3)
            delimiter = c1.selectbox("Délimiteur", [detection.delimiter, ";", ",", "\t", "|"], index=0)
            encoding = c2.text_input("Encodage", value=detection.encoding)
            decimal = c3.selectbox("Décimale", [detection.decimal, ".", ","], index=0)
            kwargs = {"delimiter": delimiter, "encoding": encoding, "decimal": decimal}
        elif suffix in ingestion.EXCEL_EXTENSIONS:
            try:
                sheets = ingestion.excel_sheets(raw)
                kwargs["sheet_name"] = st.selectbox("Feuille", sheets)
            except Exception as exc:
                st.error(f"Lecture des feuilles impossible : {exc}")
        if st.button("Prévisualiser et importer", type="primary"):
            try:
                df, info = ingestion.read_uploaded(uploaded.name, raw, **kwargs)
                if df.empty:
                    st.warning("Le fichier ne contient aucune ligne.")
                else:
                    meta = save_version(df, "RAW", info["format"], uploaded.name)
                    # Keep an immutable preview of the original imported data
                    # available after reruns and when the user returns to this
                    # page after cleaning the working STAGING version.
                    st.session_state.raw_preview = df.head(100).copy()
                    st.session_state.raw_preview_info = {
                        "source_name": uploaded.name,
                        "dataset_id": meta.dataset_id,
                        "rows": len(df),
                        "columns": len(df.columns),
                    }
                    audit.log("dataset_imported", {"name": uploaded.name, "rows": len(df), "columns": len(df.columns)}, user=st.session_state.user["username"], project_id=st.session_state.project_id)
                    st.success(f"RAW enregistré : {len(df):,} lignes × {len(df.columns)} colonnes")
            except Exception as exc:
                st.error(f"Import impossible : {exc}")

    raw_preview = st.session_state.get("raw_preview")
    raw_preview_info = st.session_state.get("raw_preview_info") or {}
    if isinstance(raw_preview, pd.DataFrame):
        st.divider()
        st.subheader("👁️ Prévisualisation de la dataset RAW")
        st.caption(
            f"Source : {raw_preview_info.get('source_name', 'dataset')} · "
            f"Version : RAW · {raw_preview_info.get('rows', len(raw_preview)):,} lignes × "
            f"{raw_preview_info.get('columns', len(raw_preview.columns))} colonnes · "
            f"aperçu limité aux {len(raw_preview):,} premières lignes."
        )
        st.dataframe(raw_preview, use_container_width=True, hide_index=True)
        if st.button("Effacer l’aperçu RAW"):
            st.session_state.raw_preview = None
            st.session_state.raw_preview_info = None
            st.rerun()

elif page == "Qualité":
    st.header("🔎 Profilage et qualité")
    df = require_df()
    profile = profiler.profile(df)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Lignes", f"{profile.summary['rows']:,}")
    c2.metric("Colonnes", profile.summary["columns"])
    c3.metric("Valeurs manquantes", f"{profile.summary['missing_pct']:.2f}%")
    c4.metric("Score qualité", f"{profile.quality_score:.1f}/100")
    for warning in profile.warnings: st.warning(warning)
    st.dataframe(profile.columns, use_container_width=True, hide_index=True)
    if st.button("Ajouter le profil au rapport"):
        st.session_state.analysis_results.append({"title":"Profil qualité", "data": profile.columns, "answer": f"Score qualité {profile.quality_score}/100"})
        st.success("Ajouté au rapport.")
    st.subheader("Règles métier de qualité")
    rtype=st.selectbox("Règle",["not_null","unique","non_negative","allowed_values","date_order"])
    rule=None
    if rtype=="date_order":
        a=st.selectbox("Date début",list(df.columns),key="rule_start"); b=st.selectbox("Date fin",list(df.columns),key="rule_end"); rule={"type":rtype,"start_column":a,"end_column":b}
    else:
        c=st.selectbox("Colonne",list(df.columns),key="rule_col"); rule={"type":rtype,"column":c}
        if rtype=="allowed_values":
            values=st.text_input("Valeurs autorisées séparées par |",value="Auto|MRH|Santé"); rule["values"]=[x.strip() for x in values.split("|") if x.strip()]
    if st.button("Tester la règle"):
        rr=quality_rules.evaluate(df,[rule])[0]
        (st.success if rr.passed else st.error)(f"{rr.message} — violations: {rr.violations} ({rr.violation_pct:.2f}%)")

elif page == "Nettoyage":
    st.header("🧹 Nettoyage et transformation")
    df = require_df()
    action = st.selectbox("Action", ["Normaliser noms de colonnes","Supprimer doublons","Renommer colonne","Changer type","Imputer NA","Standardiser catégories","Filtrer lignes"])
    if action == "Normaliser noms de colonnes":
        if st.button("Appliquer"):
            out=cleaner.normalize_column_names(df); log_transform("normalize_columns",df,out.dataframe,parameters=out.details); st.session_state.df=out.dataframe; st.session_state.stage="STAGING"; st.success("Noms normalisés."); st.rerun()
    elif action == "Supprimer doublons":
        subset = st.multiselect("Clé de déduplication (vide = ligne complète)", list(df.columns))
        if st.button("Prévisualiser / appliquer"):
            out=cleaner.drop_duplicates(df,subset=subset or None); log_transform("drop_duplicates",df,out.dataframe,parameters=out.details); st.session_state.df=out.dataframe; st.session_state.stage="STAGING"; st.success(f"{out.changed_rows} doublon(s) supprimé(s)."); st.rerun()
    elif action == "Renommer colonne":
        col=st.selectbox("Colonne",list(df.columns)); new_name=st.text_input("Nouveau nom")
        if st.button("Appliquer") and new_name:
            out=cleaner.rename_columns(df,{col:new_name}); log_transform("rename",df,out.dataframe,column=col,parameters=out.details); st.session_state.df=out.dataframe; st.session_state.stage="STAGING"; st.rerun()
    elif action == "Changer type":
        col=st.selectbox("Colonne",list(df.columns)); target=st.selectbox("Type",["numeric","datetime","string","category","boolean"])
        if st.button("Appliquer"):
            out=cleaner.cast_column(df,col,target); log_transform("cast",df,out.dataframe,column=col,parameters=out.details); st.session_state.df=out.dataframe; st.session_state.stage="STAGING"; st.warning(f"Nouvelles valeurs NA dues à la conversion : {out.details.get('new_na',0)}"); st.rerun()
    elif action == "Imputer NA":
        col=st.selectbox("Colonne",list(df.columns)); strategy=st.selectbox("Stratégie",["median","mean","mode","constant","group_median"]); value=st.text_input("Valeur constante (si applicable)"); group=st.selectbox("Groupe (si group_median)",[None]+list(df.columns))
        st.warning("L'imputation modifie l'information. Validez la stratégie avec le métier avant de créer CURATED.")
        is_protected_identifier = any(
            hint == col.lower() or col.lower().endswith(f"_{hint}")
            for hint in cleaner.PROTECTED_NAME_HINTS
        )
        if is_protected_identifier:
            st.info("Cette colonne ressemble à un identifiant. L’imputation automatique est désactivée pour préserver l’intégrité des clés.")
        if st.button("Appliquer l'imputation", disabled=is_protected_identifier):
            try:
                out=cleaner.impute(df,col,strategy,value if strategy=="constant" else None,group)
                log_transform("impute",df,out.dataframe,column=col,parameters=out.details)
                st.session_state.df=out.dataframe
                st.session_state.stage="STAGING"
                st.success(f"{out.changed_rows} valeur(s) imputée(s).")
                st.rerun()
            except (KeyError, ValueError) as exc:
                st.error(str(exc))
    elif action == "Standardiser catégories":
        col=st.selectbox("Colonne",list(df.columns)); st.write(df[col].value_counts(dropna=False).head(30)); raw_mapping=st.text_area("Mapping JSON", value='{"ABIDJAN":"Abidjan","abidjan":"Abidjan"}')
        if st.button("Appliquer mapping"):
            mapping=json.loads(raw_mapping); out=cleaner.standardize_categories(df,col,mapping); log_transform("standardize_categories",df,out.dataframe,column=col,parameters=out.details); st.session_state.df=out.dataframe; st.session_state.stage="STAGING"; st.rerun()
    else:
        col=st.selectbox("Colonne",list(df.columns)); op=st.selectbox("Opérateur",["==","!=",">",">=","<","<=","contains"]); value=st.text_input("Valeur")
        if st.button("Appliquer filtre"):
            cast_value=value
            if pd.api.types.is_numeric_dtype(df[col]):
                try: cast_value=float(value)
                except ValueError: pass
            out=cleaner.filter_rows(df,col,op,cast_value); log_transform("filter",df,out.dataframe,column=col,parameters=out.details); st.session_state.df=out.dataframe; st.session_state.stage="STAGING"; st.rerun()

    st.divider(); st.subheader("Validation de la base nettoyée")
    if st.button("Créer la version CURATED", type="primary"):
        parent=(st.session_state.dataset_meta or {}).get("dataset_id")
        meta=save_version(df.copy(),"CURATED","derived","validated_clean_data",parent_id=parent)
        audit.log("dataset_curated",meta.to_dict(),user=st.session_state.user["username"],project_id=st.session_state.project_id)
        st.success("Version CURATED créée. Les analyses doivent utiliser cette version.")
    c1,c2,c3=st.columns(3)
    for c,fmt in zip((c1,c2,c3),("CSV","XLSX","Parquet")):
        try:
            data,name,mime=dataframe_download(df,fmt); c.download_button(f"⬇ {fmt}",data,name,mime)
        except Exception as exc:
            c.caption(f"{fmt} indisponible: {exc}")

elif page == "Analyse IA":
    st.header("💬 Analyse en langage naturel")
    df=require_df()
    if st.session_state.stage != "CURATED": st.warning("Vous analysez une version non CURATED.")
    question=st.text_area("Question",placeholder="Ex. Quelle est la prime moyenne ? Compare les sinistres par région.")
    if st.button("Analyser",type="primary") and question.strip():
        try:
            result,plan=analysis_agent.ask(question,df)
            st.subheader(result.title); st.write(result.answer); st.code(json.dumps(plan,ensure_ascii=False,indent=2,default=str),language="json")
            if isinstance(result.data,pd.DataFrame): st.dataframe(result.data,use_container_width=True)
            else: st.metric("Résultat", str(result.data))
            if result.warnings:
                for w in result.warnings: st.warning(w)
            st.session_state.analysis_results.append({"title":result.title,"answer":result.answer,"data":result.data,"calculation":result.calculation})
            audit.log("analysis",{"question":question,"plan":plan,"calculation":result.calculation},user=st.session_state.user["username"],project_id=st.session_state.project_id)
        except Exception as exc: st.exception(exc)

elif page == "Assurance KPI":
    st.header("🛡️ KPI assurance")
    df=require_df(); cols=list(df.columns)
    kpi=st.selectbox("Indicateur",["Ratio de sinistralité","Coût moyen sinistre","Fréquence","Taux d'encaissement","Taux de cession","Taux de rétention"])
    try:
        result=None
        if kpi=="Ratio de sinistralité": result=kpi_service.loss_ratio(df,st.selectbox("Sinistres",cols),st.selectbox("Primes",cols,index=min(1,len(cols)-1)))
        elif kpi=="Coût moyen sinistre": result=kpi_service.average_claim_cost(df,st.selectbox("Montant sinistre",cols),st.selectbox("ID sinistre",[None]+cols))
        elif kpi=="Fréquence": result=kpi_service.claim_frequency(df,st.selectbox("ID sinistre",cols),st.selectbox("Exposition (optionnel)",[None]+cols))
        elif kpi=="Taux d'encaissement": result=kpi_service.collection_rate(df,st.selectbox("Primes encaissées",cols),st.selectbox("Primes émises",cols,index=min(1,len(cols)-1)))
        elif kpi=="Taux de cession": result=kpi_service.cession_rate(df,st.selectbox("Primes cédées",cols),st.selectbox("Primes brutes",cols,index=min(1,len(cols)-1)))
        elif kpi=="Taux de rétention": result=kpi_service.retention_rate(df,st.selectbox("Primes nettes",cols),st.selectbox("Primes brutes",cols,index=min(1,len(cols)-1)))
        if st.button("Calculer KPI",type="primary"):
            display=kpi_service.as_display(result); st.metric(display["label"],display["display"]); st.caption(display["formula"]); st.session_state.analysis_results.append({"title":display["label"],"answer":display["display"],"kpi":display})
    except Exception as exc: st.error(str(exc))

elif page == "Dashboard":
    st.header("📊 Dashboard")
    df=require_df(); cols=list(df.columns)
    tab1, tab2 = st.tabs(["Dashboard assurance", "Graphique libre"])
    with tab1:
        numeric_cols=list(df.select_dtypes(include="number").columns)
        if len(numeric_cols) < 2:
            st.info("Au moins deux colonnes numériques sont nécessaires pour le dashboard assurance.")
        else:
            premium_col=st.selectbox("Prime",numeric_cols,key="dash_premium")
            claims_col=st.selectbox("Sinistres",numeric_cols,index=min(1,len(numeric_cols)-1),key="dash_claims")
            group_col=st.selectbox("Dimension de segmentation",[None]+cols,key="dash_group")
            date_col=st.selectbox("Date (optionnel)",[None]+cols,key="dash_date")
            try:
                d=dashboard_service.portfolio_overview(df,premium_col=premium_col,claims_col=claims_col,group_col=group_col,date_col=date_col)
                c1,c2,c3,c4=st.columns(4)
                for c,card in zip((c1,c2,c3,c4),d.cards):
                    val=card["value"]
                    if card.get("unit")=="%" and val is not None: display=f"{val:,.2f}%"
                    elif isinstance(val,(int,float)): display=f"{val:,.2f}"
                    else: display=str(val)
                    c.metric(card["label"],display)
                if d.premium_claims_by_group is not None:
                    long=d.premium_claims_by_group.melt(id_vars=[group_col],value_vars=["premium","claims"],var_name="metric",value_name="value")
                    st.plotly_chart(px.bar(long,x=group_col,y="value",color="metric",barmode="group",title="Primes et sinistres par segment"),use_container_width=True)
                    st.dataframe(d.premium_claims_by_group,use_container_width=True)
                if d.monthly_trend is not None:
                    long=d.monthly_trend.melt(id_vars=["month"],value_vars=["premium","claims"],var_name="metric",value_name="value")
                    st.plotly_chart(px.line(long,x="month",y="value",color="metric",markers=True,title="Évolution mensuelle"),use_container_width=True)
                st.subheader("Principaux sinistres")
                st.dataframe(d.top_claims.head(10),use_container_width=True)
            except Exception as exc:
                st.error(f"Dashboard impossible : {exc}")
    with tab2:
        chart=st.selectbox("Graphique",["bar","line","histogram","scatter","box"]); x=st.selectbox("X",cols); y=st.selectbox("Y",[None]+cols)
        try:
            if chart=="histogram": fig=px.histogram(df,x=x)
            elif chart=="box": fig=px.box(df,y=y or x,x=None if y is None else x)
            elif chart=="scatter": fig=px.scatter(df,x=x,y=y)
            elif chart=="line": fig=px.line(df,x=x,y=y)
            else: fig=px.bar(df,x=x,y=y)
            st.plotly_chart(fig,use_container_width=True)
            if st.button("Ajouter ce graphique au rapport"):
                png=ChartService.matplotlib_png(df.head(5000),chart,x=x,y=y,title=f"{chart}: {x} / {y or ''}")
                st.session_state.report_charts.append({"title":f"{chart}: {x} / {y or ''}","png":png}); st.success("Graphique ajouté.")
        except Exception as exc: st.error(f"Graphique impossible : {exc}")

elif page == "Base SQL":
    st.header("🗄️ Connexion base de données")
    st.warning("Utilisez un compte READ ONLY. Les secrets ne sont jamais journalisés par l'application.")
    source_mode=st.radio("Type de source",["SQLAlchemy URL","Microsoft Access"],horizontal=True)
    if source_mode=="SQLAlchemy URL":
        url=st.text_input("URL SQLAlchemy",type="password",placeholder="postgresql+psycopg://user:password@host:5432/db")
        if st.button("Tester et connecter"):
            try:
                db=DatabaseService(); db.connect(url); st.session_state.db_service=db; st.success("Connexion réussie.")
            except Exception as exc: st.error(str(exc))
    else:
        access_file=st.file_uploader("Fichier Access .mdb/.accdb",type=["mdb","accdb"],key="access_upload")
        driver=st.text_input("Pilote ODBC",value="Microsoft Access Driver (*.mdb, *.accdb)")
        st.caption("Le pilote Microsoft Access doit être installé sur l'hôte (généralement Windows).")
        if access_file and st.button("Connecter Access"):
            try:
                pid=ensure_project(); path=store.project_dir(pid)/"datasets"/f"uploaded_{access_file.name}"; path.write_bytes(access_file.getvalue())
                db=DatabaseService(); db.connect_access(str(path),driver=driver); st.session_state.db_service=db; st.success("Connexion Access réussie.")
            except Exception as exc: st.error(str(exc))
    db=st.session_state.get("db_service")
    if isinstance(db,DatabaseService):
        try:
            schemas=db.schemas(); schema=st.selectbox("Schéma",[None]+schemas) if schemas else None; tables=db.tables(schema); table=st.selectbox("Table/vue",tables)
            if table and st.button("Charger la table"):
                df=db.read_table(table,schema,max_rows=100000); save_version(df,"RAW","database",f"{schema}.{table}" if schema else table); st.success(f"{len(df):,} lignes chargées.")
            query=st.text_area("Requête SELECT/WITH (lecture seule)",value="SELECT 1 AS test")
            if st.button("Exécuter requête"):
                dfq=db.read_query(query); st.session_state["sql_query_result"] = dfq
            dfq=st.session_state.get("sql_query_result")
            if isinstance(dfq,pd.DataFrame):
                st.dataframe(dfq.head(200),use_container_width=True)
                if st.button("Utiliser ce résultat comme dataset"):
                    save_version(dfq.copy(),"RAW","sql_query","custom_query"); st.session_state.pop("sql_query_result",None); st.rerun()
        except Exception as exc: st.error(str(exc))

elif page == "Rapports":
    st.header("📑 Rapports multi-formats")
    df=require_df()
    if "report_summary" not in st.session_state:
        st.session_state.report_summary = "Rapport généré à partir de la version active du dataset."
    if "report_findings" not in st.session_state:
        st.session_state.report_findings = ""
    if "report_recommendations" not in st.session_state:
        st.session_state.report_recommendations = ""
    if llm.enabled and st.button("✨ Préparer synthèse et messages clés avec Gemini"):
        compact=[]
        for item in st.session_state.analysis_results[-12:]:
            compact.append({"title":item.get("title"),"answer":item.get("answer"),"calculation":item.get("calculation"),"kpi":item.get("kpi")})
        prompt=f"""
Tu es un analyste assurance. À partir UNIQUEMENT des résultats structurés ci-dessous, produis en français :
1) une synthèse exécutive de 5 à 8 phrases ;
2) 3 à 6 constats ;
3) 3 à 6 recommandations prudentes.
N'invente aucun chiffre. Sépare les sections avec SYNTHÈSE:, CONSTATS:, RECOMMANDATIONS:.
Résultats: {json.dumps(compact,ensure_ascii=False,default=str)}
"""
        try:
            r=llm.generate(prompt)
            text=r.text.strip()
            syn=text; findings_text=""; recs_text=""
            if "CONSTATS:" in text:
                syn, rest=text.split("CONSTATS:",1)
                syn=syn.replace("SYNTHÈSE:","").strip()
                if "RECOMMANDATIONS:" in rest:
                    findings_text,recs_text=rest.split("RECOMMANDATIONS:",1)
                else:
                    findings_text=rest
            st.session_state.report_summary=syn.strip()
            st.session_state.report_findings="\n".join(x.strip("•- ") for x in findings_text.splitlines() if x.strip())
            st.session_state.report_recommendations="\n".join(x.strip("•- ") for x in recs_text.splitlines() if x.strip())
            st.success(f"Synthèse préparée avec {r.model}.")
            st.rerun()
        except Exception as exc:
            st.error(f"Gemini indisponible : {exc}")
    title=st.text_input("Titre",value="Rapport AI Insurance Data Analyst")
    subtitle=st.text_input("Sous-titre",value=st.session_state.project_name or "Analyse assurance")
    summary=st.text_area("Synthèse exécutive",key="report_summary")
    findings=st.text_area("Constats (1 par ligne)",key="report_findings")
    recommendations=st.text_area("Recommandations (1 par ligne)",key="report_recommendations")
    kpis=[x["kpi"] for x in st.session_state.analysis_results if "kpi" in x]
    tables=[{"title":x["title"],"data":x["data"]} for x in st.session_state.analysis_results if isinstance(x.get("data"),pd.DataFrame)]
    payload=ReportPayload(title=title,subtitle=subtitle,executive_summary=summary,kpis=kpis,tables=tables,findings=[x for x in findings.splitlines() if x.strip()],recommendations=[x for x in recommendations.splitlines() if x.strip()],charts=st.session_state.report_charts,sources=[str((st.session_state.dataset_meta or {}).get("source_name","dataset"))],metadata={"project":st.session_state.project_name,"stage":st.session_state.stage,"generated_at":datetime.now().isoformat(timespec="seconds")})
    st.write(f"KPI: {len(kpis)} | Tableaux: {len(tables)} | Graphiques: {len(st.session_state.report_charts)}")
    if st.button("Préparer les rapports",type="primary"):
        st.session_state.generated_reports={"HTML":reporter.html(payload),"PDF":reporter.pdf(payload),"DOCX":reporter.docx(payload),"PPTX":reporter.pptx(payload),"XLSX":reporter.xlsx(payload,df)}; audit.log("reports_generated",{"formats":list(st.session_state.generated_reports)},user=st.session_state.user["username"],project_id=st.session_state.project_id); st.success("Rapports générés.")
    for fmt,data in st.session_state.get("generated_reports",{}).items():
        mime={"HTML":"text/html","PDF":"application/pdf","DOCX":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","PPTX":"application/vnd.openxmlformats-officedocument.presentationml.presentation","XLSX":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}[fmt]
        st.download_button(f"⬇ Télécharger {fmt}",data=data,file_name=f"report.{fmt.lower() if fmt!='DOCX' else 'docx'}",mime=mime)

elif page == "Audit":
    st.header("🧾 Audit et lineage")
    pid=st.session_state.project_id
    if pid:
        st.subheader("Transformations"); st.dataframe(pd.DataFrame(store.transformation_history(pid)),use_container_width=True)
        st.subheader("Événements"); st.dataframe(pd.json_normalize(audit.recent(200,pid)),use_container_width=True)
    else: st.info("Aucun projet actif.")

elif page == "Paramètres":
    st.header("⚙️ Paramètres")
    st.write("**Environnement :**",settings.app_env)
    st.write("**Gemini activé :**",llm.enabled)
    st.write("**Ordre des modèles :**", " → ".join(settings.gemini_models))
    st.write("**Taille max upload :**",f"{settings.max_upload_mb} MB")
    st.code("GOOGLE_API_KEY doit être défini via variable d'environnement / secret manager. Ne jamais l'inscrire dans le dépôt.")
