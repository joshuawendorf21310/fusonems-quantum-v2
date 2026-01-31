"use client";

import React from 'react';
import ProtectedRoute from '@/components/ProtectedRoute.jsx';
import { FACILITY_ROLES } from '../facilityRoles';
// TODO: Import FormBuilder, SignaturePad

const ABDForm = () => {
  // TODO: Checkbox form, explanations, patient signature, track acceptance
  return (
    <ProtectedRoute allowedRoles={FACILITY_ROLES}>
      <div>
        <h1>Advance Beneficiary Notice (ABD)</h1>
        {/* <FormBuilder /> */}
        {/* <SignaturePad /> */}
        {/* TODO: Checkbox form, explanations, signature, acceptance tracking */}
        {/* TODO: Submit to backend transport API */}
      </div>
    </ProtectedRoute>
  );
};

export default ABDForm;
