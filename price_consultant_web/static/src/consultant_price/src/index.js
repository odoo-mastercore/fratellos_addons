import React from 'react';
import ReactDOM from 'react-dom';
import Consultant from './component/consultant';

let consultant_component = document.getElementById('consultant')

if(!!consultant_component){
  ReactDOM.render(
    <Consultant />,
    consultant_component
  )
}