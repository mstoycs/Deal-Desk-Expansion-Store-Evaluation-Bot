// Eddie the Expansion Store Evaluator - Frontend JavaScript

// Admin password
const ADMIN_PASSWORD = 'DealDesk1234';
let isAdminMode = false;
let lastEvaluationData = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing Eddie...');
    
    // Get DOM elements
    const form = document.getElementById('evaluationForm');
    const evaluateBtn = document.getElementById('evaluateBtn');
    const adminTabLink = document.getElementById('adminTabLink');
    const adminPasswordModal = new bootstrap.Modal(document.getElementById('adminPasswordModal'));
    const adminPasswordSubmit = document.getElementById('adminPasswordSubmit');
    const adminPasswordInput = document.getElementById('adminPassword');
    const adminPasswordError = document.getElementById('adminPasswordError');
    const backToMainBtn = document.getElementById('backToMainBtn');
    const mainInterface = document.getElementById('mainInterface');
    const adminInterface = document.getElementById('adminInterface');

    // Handle admin tab click
    adminTabLink.addEventListener('click', function(e) {
        e.preventDefault();
        if (isAdminMode) {
            showAdminInterface();
        } else {
            adminPasswordModal.show();
        }
    });

    // Handle admin password submission
    adminPasswordSubmit.addEventListener('click', function() {
        const password = adminPasswordInput.value;
        if (password === ADMIN_PASSWORD) {
            isAdminMode = true;
            adminPasswordModal.hide();
            adminPasswordInput.value = '';
            adminPasswordError.classList.add('d-none');
            showAdminInterface();
        } else {
            adminPasswordError.classList.remove('d-none');
        }
    });

    // Handle Enter key in password field
    adminPasswordInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            adminPasswordSubmit.click();
        }
    });

    // Handle back to main button
    backToMainBtn.addEventListener('click', function() {
        showMainInterface();
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        await evaluateStores();
    });

    async function evaluateStores() {
        try {
            // Clear previous results
            clearResults();
            
            // Show loading state
            evaluateBtn.disabled = true;
            evaluateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Evaluating...';
            
            // Get form data
            const mainStoreUrl = document.getElementById('mainStoreUrl').value.trim();
            const expansionStoreUrl = document.getElementById('expansionStoreUrl').value.trim();
            const mainStoreType = document.querySelector('input[name="mainStoreType"]:checked')?.value || 'd2c';
            const expansionStoreType = document.querySelector('input[name="expansionStoreType"]:checked')?.value || 'd2c';
            
            // Validate inputs
            if (!mainStoreUrl || !expansionStoreUrl) {
                displayError('Please enter both main store URL and expansion store URL.');
                return;
            }
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => {
                controller.abort();
            }, 60000); // 60 second timeout
            
            const response = await fetch('/evaluate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    main_store_url: mainStoreUrl,
                    expansion_store_url: expansionStoreUrl,
                    main_store_type: mainStoreType,
                    expansion_store_type: expansionStoreType
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            lastEvaluationData = data; // Store for admin view
            
            if (isAdminMode && adminInterface.style.display !== 'none') {
                displayAdminResults(data);
            } else {
                displaySimplifiedResults(data);
            }
            
        } catch (error) {
            console.error('Error:', error);
            if (error.name === 'AbortError') {
                displayError('Evaluation timed out. Please try again with different URLs or check your internet connection.');
            } else {
                displayError('An error occurred while evaluating the expansion store. Please try again.');
            }
        } finally {
            evaluateBtn.disabled = false;
            evaluateBtn.innerHTML = '<i class="fas fa-play me-2"></i>Evaluate Expansion Store';
        }
    }

    function displaySimplifiedResults(data) {
        // Show results section
        document.getElementById('resultsSection').style.display = 'block';
        
        // Box 1: Store Information
        displayStoreInformation(data);
        
        // Box 2: Criteria Results  
        displayCriteriaResults(data);
        
        // Box 3: B2B Product Analysis (if applicable)
        displayB2BProductAnalysisBox(data);
        
        // Box 4: Next Steps
        displayNextSteps(data);
    }

    function displayStoreInformation(data) {
        const storeInfoBox = document.getElementById('storeInfoBox');
        const mainStoreInfo = document.getElementById('mainStoreInfo');
        const expansionStoreInfo = document.getElementById('expansionStoreInfo');
        
        // Get URLs from form inputs
        const mainStoreUrl = document.getElementById('mainStoreUrl').value.trim();
        const expansionStoreUrl = document.getElementById('expansionStoreUrl').value.trim();
        const mainStoreType = document.querySelector('input[name="mainStoreType"]:checked')?.value || 'd2c';
        const expansionStoreType = document.querySelector('input[name="expansionStoreType"]:checked')?.value || 'd2c';
        
        mainStoreInfo.innerHTML = `
            <p><strong>URL:</strong> <a href="${mainStoreUrl}" target="_blank" class="text-decoration-none">${mainStoreUrl}</a></p>
            <p><strong>Store Type:</strong> <span class="badge ${mainStoreType === 'd2c' ? 'bg-primary' : 'bg-info'}">${mainStoreType.toUpperCase()}</span></p>
        `;
        
        expansionStoreInfo.innerHTML = `
            <p><strong>URL:</strong> <a href="${expansionStoreUrl}" target="_blank" class="text-decoration-none">${expansionStoreUrl}</a></p>
            <p><strong>Store Type:</strong> <span class="badge ${expansionStoreType === 'd2c' ? 'bg-primary' : 'bg-info'}">${expansionStoreType.toUpperCase()}</span></p>
        `;
        
        storeInfoBox.style.display = 'block';
    }

    function displayCriteriaResults(data) {
        const criteriaBox = document.getElementById('criteriaBox');
        const criteriaResults = document.getElementById('criteriaResults');
        
        // Define the 4 main criteria with user-friendly names
        const mainCriteria = [
            {
                key: 'brand_extension',
                name: 'The Expansion Store is a clear extension of the Main Store',
                met: data.criteria_met?.brand_extension || false
            },
            {
                key: 'branding_identical', 
                name: 'The Expansion Store must be identical to the Main Store with respect to the Store name and other branding',
                met: data.criteria_met?.branding_identical || false
            },
            {
                key: 'products_identical',
                name: 'The Expansion Store must carry the same goods, products, and/or services as the Main Store',
                met: data.criteria_met?.products_identical || false
            },
            {
                key: 'language_currency_different',
                name: 'The Expansion Store may be in a different language or currency than the Main Store',
                met: true // This is always considered met as it's a "may" requirement
            }
        ];
        
        let html = '<div class="row">';
        
        mainCriteria.forEach(criteria => {
            const icon = criteria.met ? '✅' : '❌';
            const bgClass = criteria.met ? 'bg-success' : 'bg-danger';
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="d-flex align-items-start">
                        <span class="me-3" style="font-size: 1.5em;">${icon}</span>
                        <div>
                            <p class="mb-1">${criteria.name}</p>
                            <span class="badge ${bgClass}">${criteria.met ? 'Met' : 'Not Met'}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        criteriaResults.innerHTML = html;
        criteriaBox.style.display = 'block';
    }

    function displayB2BProductAnalysisBox(data) {
        const b2bProductAnalysisBox = document.getElementById('b2bProductAnalysisBox');
        const b2bProductAnalysisExplanation = document.getElementById('b2bProductAnalysisExplanation');
        
        // Check if this is a B2B evaluation where products criteria failed but store is still qualified
        const expansionStoreType = document.querySelector('input[name="expansionStoreType"]:checked')?.value || 'd2c';
        const isB2BExpansion = expansionStoreType === 'b2b';
        const isQualified = data.result === 'qualified';
        const productsIdenticalFailed = !data.criteria_met?.products_identical;
        
        // Show B2B analysis box if it's a B2B expansion store that's qualified but products criteria failed
        if (isB2BExpansion && isQualified && productsIdenticalFailed) {
            // Determine reasons based on the evaluation data
            const reasons = {
                'Products are gated behind password protected access': false,
                'Pricing for products is gated behind password protected access': false,
                'The Checkout Cart is gated behind password protected access': false
            };
            
            // Check evaluation details for B2B qualification indicators
            const b2bQualified = data.criteria_met?.b2b_qualified;
            const b2bAnalysis = data.criteria_analysis?.b2b_qualified;
            
            if (b2bQualified && b2bAnalysis) {
                // Look for specific B2B indicators in the analysis
                const detectedIndicators = b2bAnalysis.evaluation_details?.detected_indicators || [];
                const expansionStoreUrl = data.store_info?.url || '';
                const expansionStoreEvidence = b2bAnalysis.expansion_store_evidence || {};
                
                // Check for actual password-protected access (HTTP 401, login required errors)
                const hasPasswordProtectedAccess = expansionStoreEvidence.description?.includes('401') || 
                                                 expansionStoreEvidence.description?.includes('login required') ||
                                                 expansionStoreEvidence.description?.includes('authentication required');
                
                // Check if site returned 401 or similar access errors during scraping
                const totalProducts = data.criteria_analysis?.products_identical?.expansion_store_evidence?.total_products || 0;
                const hasAccessRestrictions = totalProducts === 0 && hasPasswordProtectedAccess;
                
                // Only approve based on confirmed password protection, not just URL indicators
                if (hasAccessRestrictions || hasPasswordProtectedAccess) {
                    reasons['Products are gated behind password protected access'] = true;
                    reasons['Pricing for products is gated behind password protected access'] = true;
                    reasons['The Checkout Cart is gated behind password protected access'] = true;
                } else {
                    // If it's just URL indicators without confirmed gating, don't auto-approve
                    // Check for specific evidence of gating in the evaluation details
                    const evaluationDetails = b2bAnalysis.evaluation_details || {};
                    
                    // Look for confirmed gating evidence
                    if (evaluationDetails.b2b_requirements && 
                        evaluationDetails.b2b_requirements.includes('Requires login for cart functionality')) {
                        reasons['The Checkout Cart is gated behind password protected access'] = true;
                    }
                    
                    if (evaluationDetails.b2b_requirements && 
                        evaluationDetails.b2b_requirements.includes('Pricing not publicly visible')) {
                        reasons['Pricing for products is gated behind password protected access'] = true;
                    }
                    
                    // Only mark products as gated if we have actual evidence, not just URL patterns
                    if (hasPasswordProtectedAccess || 
                        (detectedIndicators.length > 0 && totalProducts === 0 && hasAccessRestrictions)) {
                        reasons['Products are gated behind password protected access'] = true;
                    }
                }
            }
            
            // Build the explanation HTML
            let explanationHTML = `
                <div class="alert alert-warning">
                    <p class="mb-3"><strong>B2B Store Detected:</strong> This expansion store has been identified as a Business-to-Business (B2B) site. Product analysis was limited due to access restrictions typical of B2B platforms.</p>
                </div>
                <div class="row">
            `;
            
            // Add each reason with appropriate icon
            for (const [reason, isTrue] of Object.entries(reasons)) {
                const icon = isTrue ? '✅' : '❌';
                const textClass = isTrue ? 'text-success' : 'text-muted';
                
                explanationHTML += `
                    <div class="col-12 mb-2">
                        <div class="d-flex align-items-center">
                            <span class="me-3" style="font-size: 1.2em;">${icon}</span>
                            <span class="${textClass}">${reason}</span>
                        </div>
                    </div>
                `;
            }
            
            explanationHTML += `
                </div>
                <div class="alert alert-info mt-3">
                    <p class="mb-0"><strong>Why this store is still qualified:</strong> B2B expansion stores follow different evaluation criteria. When cart functionality and pricing require login access (indicating a qualified B2B model), the store can qualify even without public product analysis.</p>
                </div>
            `;
            
            b2bProductAnalysisExplanation.innerHTML = explanationHTML;
            b2bProductAnalysisBox.style.display = 'block';
        } else {
            b2bProductAnalysisBox.style.display = 'none';
        }
    }

    function displayNextSteps(data) {
        const nextStepsBox = document.getElementById('nextStepsBox');
        const finalResult = document.getElementById('finalResult');
        const nextStepsContent = document.getElementById('nextStepsContent');
        
        const isQualified = data.result === 'qualified';
        
        // Final Result
        if (isQualified) {
            finalResult.innerHTML = `
                <div class="alert alert-success text-center mb-4">
                    <h4 class="mb-0">
                        <i class="fas fa-check-circle me-2"></i>
                        Qualified Expansion Store
                    </h4>
                </div>
            `;
            
            // Next steps for qualified stores
            nextStepsContent.innerHTML = `
                <div class="row">
                    <div class="col-md-4 mb-3">
                        <div class="card border-primary">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0"><i class="fas fa-user-tie me-2"></i>Sales Reps (New Business)</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">Continue with the new Plus opportunity in Salesforce & Ironclad</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-3">
                        <div class="card border-info">
                            <div class="card-header bg-info text-white">
                                <h6 class="mb-0"><i class="fas fa-users me-2"></i>MSM/LE</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">Continue with the MSM Expansion Store Addition Request (<a href="#" target="_blank">Guru card here</a>) process</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-3">
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <h6 class="mb-0"><i class="fas fa-headset me-2"></i>PSS/KAS</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">Follow the Plus Support - Expansion Stores process in this <a href="#" target="_blank">Guru card</a></p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            finalResult.innerHTML = `
                <div class="alert alert-danger text-center mb-4">
                    <h4 class="mb-0">
                        <i class="fas fa-times-circle me-2"></i>
                        Unqualified Expansion Store
                    </h4>
                </div>
            `;
            
            // Next steps for unqualified stores
            nextStepsContent.innerHTML = `
                <div class="card border-warning">
                    <div class="card-body">
                        <h5 class="card-title text-warning">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Action Required
                        </h5>
                        <p class="mb-3">The requested store does not qualify as an expansion store and should be sold at Shopify current Plus fees.</p>
                        <div class="alert alert-info">
                            <p class="mb-0">
                                <strong>Exception Process:</strong> If the requested store is tied to a merchant with $50M+ GMV (net new or existing Shopify merchants) and you would like to request an exception, please submit a Deal Desk case in Banff following the process noted in this <a href="#" target="_blank">Guru card</a>.
                            </p>
                        </div>
                        <div class="text-center">
                            <strong>Please submit a case to Deal Desk to discuss Plus licensing options for the merchant.</strong>
                        </div>
                    </div>
                </div>
            `;
        }
        
        nextStepsBox.style.display = 'block';
    }

    function displayAdminResults(data) {
        // Show admin interface content with all the detailed analysis
        const adminStoreInfo = document.getElementById('admin-store-info');
        const adminCriteriaResults = document.getElementById('admin-criteria-results');
        const adminProductAnalysis = document.getElementById('admin-product-analysis');
        const adminReasonsRecommendations = document.getElementById('admin-reasons-recommendations');
        
        // Store Information (clean admin view)
        const mainStoreInfo = data.criteria_analysis?.branding_identical?.main_store_evidence || {};
        const mainStoreLanguageCurrency = data.criteria_analysis?.language_currency?.main_store_evidence || {};
        const expansionStoreLanguageCurrency = data.criteria_analysis?.language_currency?.expansion_store_evidence || {};
        
        adminStoreInfo.innerHTML = `
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">📊 Detailed Store Information</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-primary mb-3">🏪 Main Store</h6>
                            <div class="info-grid">
                                <div class="info-item mb-3">
                                    <strong>Store Name:</strong>
                                    <div class="mt-1">${mainStoreInfo.store_name || 'Not detected'}</div>
                                </div>
                                <div class="info-item mb-3">
                                    <strong>Store URL:</strong>
                                    <div class="mt-1"><a href="${data.main_store_url || mainStoreInfo.url}" target="_blank" class="text-decoration-none">${data.main_store_url || mainStoreInfo.url}</a></div>
                                </div>
                                <div class="info-item mb-3">
                                    <strong>Business Type:</strong>
                                    <div class="mt-1"><span class="badge ${data.main_store_type === 'd2c' ? 'bg-primary' : 'bg-info'}">${(data.main_store_type || 'Unknown').toUpperCase()}</span></div>
                                </div>
                                <div class="info-item mb-3">
                                    <strong>Store Default Language:</strong>
                                    <div class="mt-1">${mainStoreLanguageCurrency.language || 'Not detected'}</div>
                                </div>
                                <div class="info-item mb-3">
                                    <strong>Store Default Currency:</strong>
                                    <div class="mt-1">${mainStoreLanguageCurrency.currency || 'Not detected'}</div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-success mb-3">🏪 Expansion Store</h6>
                            <div class="info-grid">
                                <div class="info-item mb-3">
                                    <strong>Store Name:</strong>
                                    <div class="mt-1">${data.store_info.store_name || 'Not detected'}</div>
                                </div>
                                <div class="info-item mb-3">
                                    <strong>Store URL:</strong>
                                    <div class="mt-1"><a href="${data.store_info.url}" target="_blank" class="text-decoration-none">${data.store_info.url}</a></div>
                                </div>
                                <div class="info-item mb-3">
                                    <strong>Business Type:</strong>
                                    <div class="mt-1"><span class="badge ${data.store_info.business_type === 'd2c' ? 'bg-primary' : 'bg-info'}">${data.store_info.business_type.toUpperCase()}</span></div>
                                </div>
                                <div class="info-item mb-3">
                                    <strong>Store Default Language:</strong>
                                    <div class="mt-1">${expansionStoreLanguageCurrency.language || 'Not detected'}</div>
                                </div>
                                <div class="info-item mb-3">
                                    <strong>Store Default Currency:</strong>
                                    <div class="mt-1">${expansionStoreLanguageCurrency.currency || 'Not detected'}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Detailed Criteria Analysis (all current detail)
        let criteriaHtml = `
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">📋 Detailed Criteria Analysis</h5>
                </div>
                <div class="card-body">
        `;
        
        if (data.criteria_analysis) {
            for (const [criteriaKey, analysis] of Object.entries(data.criteria_analysis)) {
                const isMet = data.criteria_met[criteriaKey];
                const statusIcon = isMet ? '✅' : '❌';
                const statusClass = isMet ? 'success' : 'danger';
                
                criteriaHtml += `
                    <div class="criteria-section mb-4 p-3 border rounded">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <h6 class="mb-0">
                                ${statusIcon} ${analysis.criteria_name}
                            </h6>
                            <span class="badge bg-${statusClass}">${isMet ? 'Met' : 'Not Met'}</span>
                        </div>
                        
                        <div class="criteria-summary mb-3">
                            <p class="mb-2"><strong>Summary:</strong> ${analysis.summary}</p>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="evidence-card">
                                    <h6 class="text-primary">🏪 Main Store Evidence</h6>
                                    <div class="evidence-content">
                                        ${formatEvidence(analysis.main_store_evidence)}
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="evidence-card">
                                    <h6 class="text-success">🏪 Expansion Store Evidence</h6>
                                    <div class="evidence-content">
                                        ${formatEvidence(analysis.expansion_store_evidence)}
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${formatEvaluationDetails(analysis.evaluation_details)}
                    </div>
                `;
            }
        }
        
        criteriaHtml += `
                </div>
            </div>
        `;
        
        adminCriteriaResults.innerHTML = criteriaHtml;
        
        // Product Analysis (if available)
        if (data.product_analysis) {
            adminProductAnalysis.innerHTML = displayProductAnalysisAdmin(data.product_analysis);
        }
        
        // Reasons and Recommendations
        adminReasonsRecommendations.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Evaluation Reasons</h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-group list-group-flush">
                                ${data.reasons.map(reason => `<li class="list-group-item">${reason}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Recommendations</h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-group list-group-flush">
                                ${data.recommendations.map(rec => `<li class="list-group-item">${rec}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Show all admin sections
        adminStoreInfo.style.display = 'block';
        adminCriteriaResults.style.display = 'block';
        if (data.product_analysis) {
            adminProductAnalysis.style.display = 'block';
        }
        adminReasonsRecommendations.style.display = 'block';
    }

    function displayProductAnalysisAdmin(productAnalysis) {
        return `
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">🔍 Detailed Product Analysis</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <strong>Total Matching Products Found:</strong> ${productAnalysis.total_matches_found} / 3 required
                        ${productAnalysis.extraction_method ? `<br><small><strong>Extraction Method:</strong> ${productAnalysis.extraction_method}</small>` : ''}
                        ${productAnalysis.platform_detected ? `<br><small><strong>Platforms Detected:</strong> ${productAnalysis.platform_detected}</small>` : ''}
                        ${productAnalysis.data_freshness ? `<br><small><strong>Data Freshness:</strong> <span class="badge ${getDataFreshnessBadgeClass(productAnalysis.data_freshness)}">${productAnalysis.data_freshness}</span></small>` : ''}
                        ${productAnalysis.confidence_score ? `<br><small><strong>Confidence Score:</strong> <span class="badge ${getConfidenceBadgeClass(productAnalysis.confidence_score)}">${Math.round(productAnalysis.confidence_score * 100)}%</span></small>` : ''}
                        ${productAnalysis.last_verified ? `<br><small><strong>Last Verified:</strong> ${productAnalysis.last_verified}</small>` : ''}
                    </div>
                    
                    ${productAnalysis.matching_products && productAnalysis.matching_products.length > 0 ? `
                        <h6>Identically Named Products:</h6>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Main Store Product</th>
                                        <th>Expansion Store Product</th>
                                        <th>Match Confidence</th>
                                        <th>Links</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${productAnalysis.matching_products.map(match => `
                                        <tr>
                                            <td>
                                                <strong>${match.main_store_product}</strong>
                                                ${match.main_store_price ? `<br><small class="text-muted">${match.main_store_price}</small>` : ''}
                                            </td>
                                            <td>
                                                <strong>${match.expansion_store_product}</strong>
                                                ${match.expansion_store_price ? `<br><small class="text-muted">${match.expansion_store_price}</small>` : ''}
                                            </td>
                                            <td><span class="badge bg-success">${match.match_confidence}</span></td>
                                            <td>
                                                <div class="btn-group-vertical btn-group-sm">
                                                    ${match.main_store_url ? `<a href="${match.main_store_url}" target="_blank" class="btn btn-sm btn-outline-primary">View Main</a>` : 'No URL'}
                                                    ${match.expansion_store_url ? `<a href="${match.expansion_store_url}" target="_blank" class="btn btn-sm btn-outline-success">View Expansion</a>` : 'No URL'}
                                                </div>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : `
                        <div class="alert alert-warning">
                            <h6>No Matching Products Found</h6>
                            <p>This could be because:</p>
                            <ul>
                                <li>One or both stores don't sell products</li>
                                <li>Products don't have identical names</li>
                                <li>Product extraction was not successful</li>
                            </ul>
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    function formatEvidence(evidence) {
        let html = '';
        
        for (const [key, value] of Object.entries(evidence)) {
            if (value !== null && value !== undefined) {
                if (key === 'url') {
                    html += `<p><strong>URL:</strong> <a href="${value}" target="_blank" class="text-decoration-none">${value}</a></p>`;
                } else if (key === 'products' && Array.isArray(value) && value.length > 0) {
                    // Handle new enhanced product structure with name, url, display fields
                    if (value[0] && typeof value[0] === 'object' && value[0].hasOwnProperty('name')) {
                        html += `<p><strong>Products (showing first ${value.length}):</strong></p><ul class="list-unstyled small">`;
                        value.forEach(product => {
                            if (product.url) {
                                html += `<li>• <a href="${product.url}" target="_blank" class="text-decoration-none">${product.name}</a></li>`;
                            } else {
                                html += `<li>• ${product.name}</li>`;
                            }
                        });
                        html += `</ul>`;
                    } else {
                        // Handle legacy product format with "Name - URL" strings
                        html += `<p><strong>Products (showing first ${value.length}):</strong></p><ul class="list-unstyled small">`;
                        value.forEach(product => {
                            if (product.includes(' - https://')) {
                                const [productName, productUrl] = product.split(' - https://');
                                const fullUrl = 'https://' + productUrl;
                                html += `<li>• <a href="${fullUrl}" target="_blank" class="text-decoration-none">${productName}</a></li>`;
                            } else if (product.includes(' - http://')) {
                                const [productName, productUrl] = product.split(' - http://');
                                const fullUrl = 'http://' + productUrl;
                                html += `<li>• <a href="${fullUrl}" target="_blank" class="text-decoration-none">${productName}</a></li>`;
                            } else {
                                html += `<li>• ${product}</li>`;
                            }
                        });
                        html += `</ul>`;
                    }
                } else if (key === 'products' && Array.isArray(value) && value.length === 0) {
                    html += `<p><strong>Products:</strong> <span class="text-muted">No products found</span></p>`;
                } else if (key === 'products_analysis' && typeof value === 'string') {
                    // NEW: Handle products analysis with color-coded status boxes
                    const statusType = evidence.status_type || 'info';
                    const alertClass = statusType === 'success' ? 'alert-success' : 'alert-danger';
                    const iconClass = statusType === 'success' ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
                    
                    html += `
                        <div class="alert ${alertClass} d-flex align-items-center" role="alert">
                            <i class="bi ${iconClass} me-2"></i>
                            <div>
                                <strong>Product Search Results:</strong><br>
                                ${value}
                            </div>
                        </div>
                    `;
                    
                    // Show searched vs found products if available
                    if (evidence.searched_products && evidence.searched_products.length > 0) {
                        html += `<p><strong>Products Searched:</strong></p><ul class="list-unstyled small">`;
                        evidence.searched_products.forEach(product => {
                            html += `<li>🔍 ${product}</li>`;
                        });
                        html += `</ul>`;
                    }
                    
                    if (evidence.found_products && evidence.found_products.length > 0) {
                        html += `<p><strong>Matching Products Found:</strong></p><ul class="list-unstyled small text-success">`;
                        evidence.found_products.forEach(product => {
                            html += `<li>✅ ${product}</li>`;
                        });
                        html += `</ul>`;
                    }
                } else if (key === 'exact_matches' && Array.isArray(value)) {
                    if (value.length > 0) {
                        html += `<p><strong>Exact Matches (${value.length}):</strong></p><ul class="list-unstyled small text-success">`;
                        value.forEach(match => {
                            html += `<li>✓ ${match}</li>`;
                        });
                        html += `</ul>`;
                    } else {
                        html += `<p><strong>Exact Matches:</strong> <span class="text-muted">None found</span></p>`;
                    }
                } else if (key === 'fuzzy_matches' && Array.isArray(value)) {
                    if (value.length > 0) {
                        html += `<p><strong>Similar Matches (${value.length}):</strong></p><ul class="list-unstyled small text-warning">`;
                        value.forEach(match => {
                            html += `<li>≈ ${match}</li>`;
                        });
                        html += `</ul>`;
                    } else {
                        html += `<p><strong>Similar Matches:</strong> <span class="text-muted">None found</span></p>`;
                    }
                } else if (key === 'total_matches') {
                    html += `<p><strong>Total Matches Found:</strong> <span class="badge ${value >= 3 ? 'bg-success' : 'bg-warning'}">${value} / 3 required</span></p>`;
                } else if (key === 'analysis_summary') {
                    html += `<div class="alert ${value.includes('MET') ? 'alert-success' : 'alert-warning'} py-2"><strong>Analysis:</strong> ${value}</div>`;
                } else if (key === 'language') {
                    const source = evidence.language_source;
                    html += `<p><strong>Language:</strong> ${formatLanguageCurrency(value, source)}</p>`;
                } else if (key === 'currency') {
                    const source = evidence.currency_source;
                    html += `<p><strong>Currency:</strong> ${formatLanguageCurrency(value, source)}</p>`;
                } else if (key === 'language_source' || key === 'currency_source') {
                    // Skip these as they're handled above
                    continue;
                } else if (Array.isArray(value) && value.length > 0) {
                    html += `<p><strong>${formatKeyName(key)}:</strong> ${value.join(', ')}</p>`;
                } else if (typeof value === 'string' && value !== 'Not detected') {
                    html += `<p><strong>${formatKeyName(key)}:</strong> ${value}</p>`;
                } else if (typeof value === 'number') {
                    html += `<p><strong>${formatKeyName(key)}:</strong> ${value}</p>`;
                } else if (typeof value === 'boolean') {
                    html += `<p><strong>${formatKeyName(key)}:</strong> ${value ? '✓ Yes' : '✗ No'}</p>`;
                }
            }
        }
        
        return html;
    }
    
    // NEW: Helper functions for data freshness and confidence badges
    function getDataFreshnessBadgeClass(freshness) {
        if (freshness.includes('Real-time')) return 'bg-success';
        if (freshness.includes('Cached')) return 'bg-info';
        if (freshness.includes('Static')) return 'bg-warning';
        if (freshness.includes('Error')) return 'bg-danger';
        return 'bg-secondary';
    }
    
    function getConfidenceBadgeClass(score) {
        if (score >= 0.8) return 'bg-success';
        if (score >= 0.6) return 'bg-warning';
        return 'bg-danger';
    }
    
    // NEW: Helper function for formatting language/currency with source info
    function formatLanguageCurrency(value, source) {
        if (!value || value === 'Unknown') {
            return '<span class="text-muted">Not detected</span>';
        }
        
        const sourceText = source === 'inferred from domain' ? 
            `<small class="text-muted">(inferred from domain)</small>` : 
            source === 'detected in URL' ? 
            `<small class="text-success">(detected in URL)</small>` : '';
        
        return `${value} ${sourceText}`;
    }
    
    function formatEvaluationDetails(details) {
        if (!details || Object.keys(details).length === 0) return '';
        
        let html = '<div class="evaluation-details mt-3 p-3 bg-light rounded">';
        html += '<h6 class="text-info">🔍 Evaluation Details</h6>';
        
        for (const [key, value] of Object.entries(details)) {
            if (value !== null && value !== undefined) {
                if (Array.isArray(value)) {
                    html += `<p><strong>${formatKeyName(key)}:</strong></p><ul class="list-unstyled small">`;
                    value.forEach(item => {
                        html += `<li>• ${item}</li>`;
                    });
                    html += `</ul>`;
                } else if (typeof value === 'object') {
                    html += `<p><strong>${formatKeyName(key)}:</strong> ${JSON.stringify(value)}</p>`;
                } else {
                    html += `<p><strong>${formatKeyName(key)}:</strong> ${value}</p>`;
                }
            }
        }
        
        html += '</div>';
        return html;
    }
    
    function formatKeyName(key) {
        return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }

    function showMainInterface() {
        mainInterface.style.display = 'block';
        adminInterface.style.display = 'none';
        
        // If we have evaluation data, show simplified results
        if (lastEvaluationData) {
            displaySimplifiedResults(lastEvaluationData);
        }
    }

    function showAdminInterface() {
        mainInterface.style.display = 'none';
        adminInterface.style.display = 'block';
        
        // If we have evaluation data, show admin results
        if (lastEvaluationData) {
            displayAdminResults(lastEvaluationData);
        }
    }

    function displayError(message) {
        const errorDiv = document.getElementById('error');
        errorDiv.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading">❌ Error</h4>
                <p>${message}</p>
            </div>
        `;
        errorDiv.style.display = 'block';
        
        // Hide other sections
        document.getElementById('storeInfoBox').style.display = 'none';
        document.getElementById('criteriaBox').style.display = 'none';
        document.getElementById('nextStepsBox').style.display = 'none';
    }

    function clearResults() {
        document.getElementById('error').style.display = 'none';
        document.getElementById('storeInfoBox').style.display = 'none';
        document.getElementById('criteriaBox').style.display = 'none';
        document.getElementById('b2bProductAnalysisBox').style.display = 'none';
        document.getElementById('nextStepsBox').style.display = 'none';
        
        // Clear admin sections
        document.getElementById('admin-store-info').style.display = 'none';
        document.getElementById('admin-criteria-results').style.display = 'none';
        document.getElementById('admin-product-analysis').style.display = 'none';
        document.getElementById('admin-reasons-recommendations').style.display = 'none';
    }
});