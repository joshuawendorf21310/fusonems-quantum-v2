"use client";

import React from 'react';
import ProtectedRoute from '@/components/ProtectedRoute.jsx';
import { FACILITY_ROLES } from '../facilityRoles';
// TODO: Import FormBuilder, SignaturePad

const AOBForm = () => {
  // TODO: Insurance info, signature pad, auto-populate from MPI
  return (
    <ProtectedRoute allowedRoles={FACILITY_ROLES}>
      <div>
        <h1>Authorization of Benefits (AOB)</h1>
        {/* <FormBuilder /> */}
        {/* <SignaturePad /> */}
        {/* TODO: Insurance info, signature, auto-populate */}
        {/* TODO: Auto-populate from patient MPI backend */}
        {/* TODO: Submit to backend transport API */}
      </div>
    </ProtectedRoute>
  );
};

export default AOBForm;
