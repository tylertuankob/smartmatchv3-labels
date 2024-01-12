import streamlit as st
import pandas as pd
import json
import utils as u
from streamlit_pills import pills
import random
from streamlit_tags import st_tags
import sys
import os
from supabase import create_client, Client

def get_demo_titles(candidate):
    return candidate["grades"]["Successful Expert"] + candidate["grades"]["Expert"] + candidate["grades"]["Relevant"]

@st.cache_resource
def get_client():
    url = "https://ykzkibbnbcguemymkbzm.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlremtpYmJuYmNndWVteW1rYnptIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcwNDk3MTQ1NSwiZXhwIjoyMDIwNTQ3NDU1fQ.GoyLyzf__j5YBvy_2er6K4U5NR4NtNj26FPL1UcbOr8"
    supabase = create_client(url, key)

    return supabase

@st.cache_resource
def load_json(_client, url):
    return json.loads(_client.storage.from_("data").download(url))


@st.cache_resource
def load_json(_client, url):
    return json.loads(_client.storage.from_("data").download(url))


if __name__ == '__main__':
    client = get_client()

    demo = load_json(client, "demo_new_final.json")
    graph = load_json(client, "graph.json")
    data = load_json(client, "evaluation_data.json")

    keywords = st_tags(
        label='### Enter Name:',
        text='Type in your name as "firstname_batchnumber" such as tyler_2',
        value=[],
        suggestions=['micheal'],
        maxtags=1,
        key="batch")

    if "old_batch" not in st.session_state:
        st.session_state["old_batch"] = []

    if "batch" not in st.session_state:
        st.session_state["batch"] = []

    if len(st.session_state.batch) != len(st.session_state.old_batch):
        st.session_state.old_batch = st.session_state.batch

        if len(st.session_state.batch) == 1:
            batch = st.session_state.batch[0]
            turns = client.table('turns').select("*").eq('batch', batch).execute().data

            if len(turns) == 0:
                batch_data = random.sample(data, 10)
                for d in batch_data:
                    d["label"] = None
                    d["batch"] = batch

                client.table("turns").insert(batch_data).execute()

                turns = batch_data

            st.session_state["turns"] = turns

    if len(keywords) == 0:
        sys.exit(0)

    batch = keywords[0]

    turns = st.session_state.get("turns", [])

    GROUND_TRUTH_MODE = "truth"
    FEEDBACK_MODE = "feedback"

    i = st.select_slider('Slide to select', options=range(len(turns)))
    d = turns[i]
    candidate_id = d["candidate"]
    title = d["title"]
    mode = d["type"]
    candidate = demo[candidate_id]
    match = candidate["match"].get(title, None)

    st.title(title)
    st.subheader("Common Skills")
    st.write(" | ".join(graph["graph"][title]["skills"]))

    st.subheader("Label Action")

    if mode == GROUND_TRUTH_MODE:
        options = ["Postpone for Later", "Strong", "Acceptable", "Irrelevant"]
        label = pills("Is this candidate a match for {}?".format(title),
                      options=options,
                      index=None if d["label"] is None else options.index(d["label"]))

        client.table("turns").update({
            "label": label
        }).match({
            "candidate": d["candidate"],
            "title": d["title"],
            "batch": batch
        }).execute()

        d["label"] = label


    if mode == FEEDBACK_MODE:
        options = ["Postpone for Later", "Agree", "Acceptable", "Disagree"]
        label = pills(("This candidate will not be shown for " if title not in candidate["match"] else
                      "The matching grade for this candidate is {} for".format(candidate["match"][title]["grade"])) +
                      " {}. What do you think? \n [Successful Expert, Expert, Relevant, Irrelevant]".format(title),
                      options=options,
                      index=None if d["label"] is None else options.index(d["label"]))

        client.table("turns").update({
            "label": label
        }).match({
            "candidate": d["candidate"],
            "title": d["title"],
            "batch": batch
        }).execute()

        d["label"] = label


    st.title("Candidate Profile")

    st.subheader("Summary")
    st.write(candidate["summary"])

    if mode == FEEDBACK_MODE:
        if match is None:
            st.write("Not available")
        else:
            analytical_graph = graphviz.Digraph()
            skills_details = match["details"]["skills"]

            st.write("Matching Highlights")
            st.json([
                match["highlight_1"],
                match["highlight_2"],
                match["highlight_3"],
                match["highlight_4"],
                match["highlight_5"]
            ])

            reversed_map = {}

            for ps, ms in skills_details.items():
                if ms not in reversed_map:
                    reversed_map[ms] = []

                reversed_map[ms].append(ps)

            for ms, pss in reversed_map.items():
                st.write("Relevant skills for '{}'".format(ms))
                st.json(pss)

            st.write("List of quantitative success for this candidate")
            st.json(match["details"]["success"])

    if mode == GROUND_TRUTH_MODE:
        st.subheader("Parsed Skills")
        st.write("There are two sets of skills: domain skills and quantitative success. Domain skills are skills that the candidate possesses. Quantitative success is what the candidate has accomplished in his past that is measurable.")
        st.json(candidate["profile"]["skills"])

    st.subheader("Full Text")
    st.write(candidate["profile"]["text"]["text"].replace("\\n", "\n"))





