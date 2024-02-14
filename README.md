# StrengthPulse - A Powerlifting Performance Analyzer App

## Overview

This app provides a comprehensive analysis of powerlifting performance, focusing on Squat, Bench, and Deadlift. Users can easily benchmark their own lifting numbers against real competitors, gaining insights into their strengths and areas for improvement.

## Features

1. **Integrated ETL Pipeline:** Data provided by Openpowerlifting (https://openpowerlifting.gitlab.io/opl-csv/) is Batch Loaded into a Postgres Database and immediately available in the application
2. **User WILKS Ranking:** Calculate your WILKS score & compare it to competitors who have competed in your state
2. **Competitor Comparison:** Compare your Squat, Bench, and Deadlift numbers with data from actual competitions.
3. **Performance Benchmarking:** Gain valuable insights into your lifting performance relative to other competitors.
4. **Competitor Perfomrance Analysis:** Visualize competitor performance over time, by weight (Kg's), or by Age.

## Usage

1. **Squat Analysis:**
   - View and compare your squat performance against other competitors.

2. **Bench Analysis:**
   - Analyze your bench press numbers in comparison to competitors.

3. **Deadlift Analysis:**
   - Benchmark your deadlift performance against a pool of competitors.

## Notes

1. This application is currently under development and still working towards enriching this data
2. All data used in application has a filter on the lifter designating USA as their home country 
3. All data used in application only goes back 5 years for managing data storage and RAM requirements

## Getting Started

To get started with the app, follow these steps:

1. **Access the URL for the application**
   2. Deployed to Render @ https://strengthpulse.onrender.com/
