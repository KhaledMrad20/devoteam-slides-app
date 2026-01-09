import streamlit as st
import os
# On importe les fonctions de votre script 'generator.py'
# Assurez-vous que votre fichier de script s'appelle bien 'generator.py'
from generator_logic import generate_presentation_outline, create_presentation_file

# Configuration de la page
st.set_page_config(page_title="IA PPT Generator", page_icon="📊")

st.title("📊 Générateur de Présentation AI")
st.markdown("Entrez un sujet ou collez un texte, et l'IA créera le PowerPoint.")

# 1. Zone de saisie
user_input = st.text_area("Sujet ou Contenu du cours :", height=150)

# 2. Bouton d'action
if st.button("Générer la présentation", type="primary"):
    if not user_input:
        st.warning("Veuillez entrer du texte d'abord.")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            # Étape A : Génération du plan (Appel API)
            status_text.text("🧠 L'IA réfléchit à la structure...")
            progress_bar.progress(30)
            
            slide_data = generate_presentation_outline(user_input)
            
            # Vérification si l'API a renvoyé une erreur gérée
            if slide_data.get("presentation_title") == "Error Occurred":
                st.error(f"Erreur API : {slide_data.get('subtitle')}")
            else:
                # Étape B : Création du fichier PPTX
                status_text.text("🎨 Création des diapositives PowerPoint...")
                progress_bar.progress(70)
                
                output_file = "presentation_generee.pptx"
                final_path = create_presentation_file(slide_data, output_filename=output_file)
                
                if final_path:
                    progress_bar.progress(100)
                    status_text.text("✅ Terminé !")
                    
                    # Étape C : Bouton de téléchargement
                    with open(final_path, "rb") as file:
                        st.download_button(
                            label="📥 Télécharger le PowerPoint (.pptx)",
                            data=file,
                            file_name=output_file,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        )
                        
                    # Prévisualisation JSON (Optionnel, pour debug)
                    with st.expander("Voir la structure générée (Debug)"):
                        st.json(slide_data)
                else:
                    st.error("Erreur lors de la création du fichier PPTX.")
                    
        except Exception as e:
            st.error(f"Une erreur inattendue est survenue : {e}")

# Sidebar info
st.sidebar.info("Assurez-vous que votre clé API est bien dans le fichier .env")

