
import { getApiUrl } from "../utils/api";

/**
 * Classify an issue using HYBRID model (image + text)
 * @param {string} imageBase64 - Base64 encoded image
 * @param {string} title - Issue title
 * @param {string} description - Issue description
 * @param {Function} getAuthHeaders - Function to get authentication headers
 * @returns {Promise<Object>} - Classification result
 */
export async function classifyImage(
  imageBase64,
  title = "",
  description = "",
  getAuthHeaders = null
) {
  try {
    // Prepare headers
    const headers = {
      "Content-Type": "application/json",
    };

    // Add auth headers if available
    if (getAuthHeaders && typeof getAuthHeaders === "function") {
      const authHeaders = await getAuthHeaders();
      Object.assign(headers, authHeaders);
    }

    // Call the HYBRID ML prediction endpoint
    const response = await fetch(getApiUrl("/ml/predict/"), {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        image_base64: imageBase64,
        title: title,
        description: description,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("ML prediction failed:", errorData);

      // Fall back to "Manual"
      console.warn("Falling back to Manual classification due to ML API error");
      return {
        department: "Manual",
        confidence: 0,
        is_valid: false,
        reason: "API_ERROR",
        method: "MANUAL_FALLBACK",
      };
    }

    const result = await response.json();

    if (import.meta.env.DEV) {
      console.log("🔀 HYBRID ML Prediction Result:", {
        department: result.department,
        confidence: result.confidence,
        is_valid: result.is_valid,
        method: result.method,
        reason: result.reason,
      });
    }

    // Return the full response object
    return {
      department: result.department || "Manual",
      confidence: result.confidence || 0,
      is_valid: result.is_valid !== false,
      reason: result.reason || null,
      method: result.method || "UNKNOWN",
      image_result: result.image_result || null,
      text_result: result.text_result || null,
    };
  } catch (error) {
    console.error("Error calling HYBRID ML classification API:", error);
    // Fall back to "Manual" if the API call fails
    return {
      department: "Manual",
      confidence: 0,
      is_valid: false,
      reason: "NETWORK_ERROR",
      method: "MANUAL_FALLBACK",
    };
  }
}

/**
 * Get a user-friendly department name
 */
export function getDepartmentDisplayName(department) {
  const departmentMap = {
    "Public Works Department": "Public Works Department (PWD)",
    "Water Board Department": "Water Board",
    "Sewage and Drainage Department": "Sewage & Drainage",
    "Sanitation Department": "Sanitation",
    "Traffic Department": "Traffic",
    Manual: "Manual Classification",
  };

  return departmentMap[department] || department;
}

/**
 * Get classification method display name
 */
export function getMethodDisplayName(method) {
  const methodMap = {
    IMAGE_ONLY: "Image Only",
    TEXT_ONLY: "Text Only",
    HYBRID_AGREEMENT: "Image + Text (Agreement)",
    HYBRID_DISAGREEMENT: "Image + Text (Resolved)",
    IMAGE_PRIORITY: "Image Priority",
    TEXT_PRIORITY: "Text Priority",
    IMAGE_FALLBACK: "Image Fallback",
    MANUAL_FALLBACK: "Manual Review Required",
    MANUAL: "Manual Classification",
  };

  return methodMap[method] || method;
}