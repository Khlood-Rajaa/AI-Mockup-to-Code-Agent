# app.py
import streamlit as st
from main import HTMLGenerator, extract_image_info, get_image_dimensions
import base64
import re

# Page setup
st.set_page_config(
    page_title="Smart HTML Converter",
    page_icon="🎨",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .step-completed {
        background: #4CAF50 !important;
        color: white !important;
    }
    .step-current {
        background: #2196F3 !important;
        color: white !important;
    }
    .step-pending {
        background: #E0E0E0 !important;
        color: #666 !important;
    }
    .step-indicator {
        padding: 10px 15px;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
        margin: 5px;
    }
    .upload-section {
        background: #F0F8FF;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #45B7D1;
        margin: 10px 0;
    }
    .dimension-info {
        background: #E8F5E8;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin: 10px 0;
    }
    .full-preview {
        border: 2px solid #ddd;
        border-radius: 10px;
        overflow: hidden;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'analysis_done' not in st.session_state:
        st.session_state.analysis_done = False

def get_step_status(current_step, step_number):
    """Determine CSS class for step indicator"""
    if step_number < current_step:
        return "step-completed"
    elif step_number == current_step:
        return "step-current" 
    else:
        return "step-pending"

def display_image_upload_section(image_info):
    """Display upload sections for each detected image"""
    st.markdown("### 📸 Upload Replacement Images")
    
    uploaded_images = {}
    
    for img_id, info in image_info.items():
        with st.container():
            st.markdown(f'<div class="upload-section">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f'**🎯 Image Area {img_id}**')
                st.write(f"**Size:** {info['width']} × {info['height']}px")
                st.write(f"**Type:** {info['description']}")
                
            with col2:
                uploaded_file = st.file_uploader(
                    f"Upload image for Area {img_id}",
                    type=['jpg', 'jpeg', 'png', 'webp', 'gif'],
                    key=f"image_upload_{img_id}"
                )
                
                if uploaded_file:
                    st.image(uploaded_file, width=150, caption=f"Uploaded for Area {img_id}")
                    uploaded_images[img_id] = uploaded_file
                    st.success(f"✅ Ready!")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    return uploaded_images

def create_full_preview_html(html_content, original_width, original_height):
    """Wrap the HTML content to display at full size without scrolling"""
    # Calculate a scaled height for the iframe to show full content
    # Use the original height but cap it at 800px for reasonable display
    display_height = min(original_height, 800)
    
    # Create a wrapper that shows the full HTML without internal scrolling
    wrapper_html = f"""
    <div style="width: 100%; height: {display_height}px; overflow: visible; transform-origin: top left;">
        <div style="transform: scale(0.8); transform-origin: top left; width: 125%;">
            {html_content}
        </div>
    </div>
    """
    return wrapper_html, display_height

def main():
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎨 Smart HTML Converter</h1>', unsafe_allow_html=True)
    st.markdown("### Upload → Analyze (Original Size) → Replace Images → Get HTML")
    
    # Step indicator
    st.markdown("### 📋 Progress")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        step1_class = get_step_status(st.session_state.step, 1)
        st.markdown(f'<div class="step-indicator {step1_class}">1. Upload Design</div>', unsafe_allow_html=True)
    
    with col2:
        step2_class = get_step_status(st.session_state.step, 2)
        st.markdown(f'<div class="step-indicator {step2_class}">2. AI Analysis</div>', unsafe_allow_html=True)
    
    with col3:
        step3_class = get_step_status(st.session_state.step, 3)
        st.markdown(f'<div class="step-indicator {step3_class}">3. Replace Images</div>', unsafe_allow_html=True)
    
    with col4:
        step4_class = get_step_status(st.session_state.step, 4)
        st.markdown(f'<div class="step-indicator {step4_class}">4. Final HTML</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Step 1: Upload Design
    if st.session_state.step == 1:
        st.markdown("## 📤 Step 1: Upload Your Design")
        
        uploaded_file = st.file_uploader(
            "Choose a design image",
            type=['jpg', 'jpeg', 'png', 'webp'],
            key="design_upload"
        )
        
        if uploaded_file:
            # Get original dimensions
            original_width, original_height = get_image_dimensions(uploaded_file)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Original Image")
                st.image(uploaded_file, use_container_width=True, caption=f"Original Size: {original_width}×{original_height}px")
            
            with col2:
                st.markdown("#### Processing Info")
                st.markdown('<div class="dimension-info">', unsafe_allow_html=True)
                st.markdown("**✅ Using Original Image Size**")
                st.markdown(f"**Dimensions:** {original_width} × {original_height} pixels")
                st.markdown("")
                st.markdown("The AI will analyze and recreate the design using the exact original proportions.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("🚀 Analyze Design (Original Size)", type="primary", use_container_width=True):
                st.session_state.original_design = uploaded_file
                st.session_state.original_width = original_width
                st.session_state.original_height = original_height
                st.session_state.step = 2
                st.rerun()
    
    # Step 2: AI Analysis
    elif st.session_state.step == 2:
        st.markdown("## 🔍 Step 2: AI Analysis")
        
        # Show dimension info
        original_width = st.session_state.original_width
        original_height = st.session_state.original_height
        st.markdown('<div class="dimension-info">', unsafe_allow_html=True)
        st.markdown(f"**📊 Analyzing at Original Size**")
        st.markdown(f"**Working with:** {original_width} × {original_height} pixels")
        st.markdown("Preserving exact proportions and layout")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if not st.session_state.analysis_done:
            with st.spinner(f"Analyzing your {original_width}×{original_height} pixel design..."):
                try:
                    generator = HTMLGenerator()
                    image_b64 = generator.encode_image(st.session_state.original_design)
                    html_with_placeholders = generator.generate_html_with_image_placeholders(
                        image_b64, original_width, original_height
                    )
                    
                    # Store results
                    st.session_state.html_with_placeholders = html_with_placeholders
                    st.session_state.image_info = extract_image_info(html_with_placeholders)
                    st.session_state.analysis_done = True
                    
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    if st.button("🔄 Try Again"):
                        st.rerun()
                    return
        
        # Show analysis results
        if st.session_state.analysis_done:
            st.success(f"✅ Analysis complete! Found {len(st.session_state.image_info)} image areas")
            
            # Show preview
            st.markdown("#### 📐 Design with Detected Image Areas")
            preview_html, preview_height = create_full_preview_html(st.session_state.html_with_placeholders, original_width, original_height)
            st.components.v1.html(preview_html, height=preview_height, scrolling=False)
            st.info("🔄 Dashed areas show where images were detected")
            
            if st.button("📸 Continue to Image Replacement", type="primary", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
    
    # Step 3: Replace Images
    elif st.session_state.step == 3:
        st.markdown("## 🖼️ Step 3: Replace Images")
        
        # Show dimension info
        st.markdown('<div class="dimension-info">', unsafe_allow_html=True)
        st.markdown(f"**🎯 Working with Original Layout**")
        st.markdown(f"**Base dimensions:** {st.session_state.original_width} × {st.session_state.original_height}px")
        st.markdown("All measurements preserve original proportions")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show preview
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Original Design")
            st.image(st.session_state.original_design, use_container_width=True)
        with col2:
            st.markdown("#### With Image Placeholders")
            preview_html, preview_height = create_full_preview_html(st.session_state.html_with_placeholders, st.session_state.original_width, st.session_state.original_height)
            st.components.v1.html(preview_html, height=preview_height, scrolling=False)
        
        # Image upload
        uploaded_images = display_image_upload_section(st.session_state.image_info)
        
        # Check if all images are uploaded
        all_uploaded = len(uploaded_images) == len(st.session_state.image_info)
        
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Analysis", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        
        with col2:
            if all_uploaded:
                if st.button("🚀 Generate Final HTML →", type="primary", use_container_width=True):
                    st.session_state.uploaded_images = uploaded_images
                    st.session_state.step = 4
                    st.rerun()
            else:
                remaining = len(st.session_state.image_info) - len(uploaded_images)
                st.button(f"Upload {remaining} More", disabled=True, use_container_width=True)
        
        if not all_uploaded:
            remaining = len(st.session_state.image_info) - len(uploaded_images)
            st.warning(f"📷 Please upload {remaining} more image(s) to continue")
    
    # Step 4: Final HTML
    elif st.session_state.step == 4:
        st.markdown("## 💻 Step 4: Final HTML")
        
        st.markdown('<div class="dimension-info">', unsafe_allow_html=True)
        st.markdown(f"**✅ Final HTML Preserves Original Size**")
        st.markdown(f"**Based on:** {st.session_state.original_width} × {st.session_state.original_height}px layout")
        st.markdown("Your images integrated while maintaining exact proportions")
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.spinner("Generating final HTML with your images..."):
            try:
                generator = HTMLGenerator()
                final_html = generator.replace_image_placeholders(
                    st.session_state.html_with_placeholders,
                    st.session_state.uploaded_images
                )
                
                st.success("🎉 Your website is ready!")
                
                # Show final result comparison - FULL PREVIEW WITHOUT SCROLLING
                st.markdown("### 🔍 Side-by-Side Comparison")
                
                # Calculate appropriate display height
                display_height = min(st.session_state.original_height, 700)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"#### Original Design")
                    st.image(st.session_state.original_design, use_container_width=True)
                    st.caption(f"Original: {st.session_state.original_width}×{st.session_state.original_height}px")
                
                with col2:
                    st.markdown("#### Final HTML Result")
                    # Create full preview without internal scrolling
                    full_preview_html = f"""
                    <div style="width: 100%; height: {display_height}px; overflow: visible; border: 1px solid #ddd; border-radius: 10px; padding: 10px; background: white;">
                        <div style="transform: scale(0.7); transform-origin: top left; width: 142.857%;">
                            {final_html}
                        </div>
                    </div>
                    """
                    st.components.v1.html(full_preview_html, height=display_height, scrolling=False)
                    st.caption("Fully rendered HTML - No scrolling needed")
                
                # Code and download
                st.markdown("---")
                st.markdown("#### 📝 HTML Code")
                with st.expander("View/Edit HTML Code", expanded=True):
                    edited_code = st.text_area("HTML Code:", value=final_html, height=300, key="final_code")
                
                # Download button
                st.download_button(
                    "💾 Download HTML File",
                    edited_code,
                    file_name="website.html",
                    mime="text/html",
                    use_container_width=True
                )
                
                # Start over
                if st.button("🔄 Start New Project", type="primary", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if st.button("← Back to Image Upload"):
                    st.session_state.step = 3
                    st.rerun()

if __name__ == "__main__":
    main()