"use client";

import React from 'react';
import ProtectedRoute from '@/components/ProtectedRoute.jsx';
import { FACILITY_ROLES } from '../facilityRoles';
// TODO: Import FormBuilder, AI suggestions

const PCSForm = () => {
  // TODO: Rich text editor, checkboxes, AI suggestions, save/submit
  return (
    <ProtectedRoute allowedRoles={FACILITY_ROLES}>
      <div>
        <h1>Patient Care Summary (PCS)</h1>
        {/* <FormBuilder /> */}
        {/* TODO: Rich text, checkboxes, AI suggestions */}
        {/* TODO: Integrate with Ollama for AI suggestions */}
        {/* TODO: Save/submit to backend transport API */}
      </div>
    </ProtectedRoute>
  );
};

export default PCSForm;
